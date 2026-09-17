#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：async_export_mixin.py
@Author  ：李小涛
@Date    ：2025/11/30 下午3:16 
@Explain : 通用异步导出视图（基于 django-import-export-extensions）
"""

from drf_spectacular.utils import extend_schema_view, extend_schema
from import_export_extensions.api import ExportJobViewSet, ExportJobSerializer
from import_export_extensions.models import ExportJob

from extends.drf.response import success_response
from extends.celery.celery_active import require_celery_active
from .sync_export_mixin import _compute_permitted_export_attrs


class CustomExportJobSerializer(ExportJobSerializer):
    """
    异步导出任务序列化类：
    仅暴露前端需要的字段，减少响应数据传输量
    """

    class Meta:
        model = ExportJob
        fields = (
            "id",
            "export_status",
            "data_file",
            "progress",
            "export_started",
            "export_finished",
            "created",
            "modified",
            "error_message",
        )


class CustomExportJobViewSet(ExportJobViewSet):
    """
    自定义异步导出任务视图集：
        - 统一返回格式（success_response）
        - 非管理员只能查看自己的导出任务
        - 动态生成 Swagger 文档（x-function 扩展）
        - 导出字段受字段级可下载权限约束
    """

    ordering = ("-id",)
    serializer_class = CustomExportJobSerializer
    export_open_api_description = (
        "该接口用于创建导出任务并立即启动。\n"
        "- 要监控任务进度，请使用任务的详情接口来获取任务状态。\n"
        "- 当状态变为 `EXPORTED` 时，即可下载导出的文件。\n"
    )

    def __init_subclass__(cls) -> None:
        """
        子类创建时动态补充 OpenAPI 文档描述

        实现说明：
        start_export_action / cancel 等动作由父类 mixin 在运行时注入，
        无法通过静态装饰器添加 extend_schema，因此需在此处动态添加。
        """
        # 先让父类（包括 ExportStartActionMixin）完成初始化
        super().__init_subclass__()
        # === 动态添加 extend_schema ===
        schema_dict = {
            "start_export_action": extend_schema(
                summary="异步导出创建",
                extensions={"x-function": "ExportStart", "x-assign_permission": False},
                responses={201: cls.serializer_class},
            ),
            "cancel": extend_schema(
                summary="异步导出取消",
                extensions={"x-function": "ExportCancel", "x-assign_permission": False},
                responses={200: {}},
            ),
        }
        extend_schema_view(**schema_dict)(cls)

    @extend_schema(summary="异步导出列表", extensions={"x-function": "ExportList", "x-assign_permission": False})
    def list(self, request, *args, **kwargs):
        """
        异步导出任务列表：
            - 管理员：获取所有导出任务的分页列表
            - 普通用户：仅获取自己的导出任务列表

        Args:
            request: 请求对象

        Returns:
            分页列表响应
        """
        user = request.user
        if not user.is_superuser:
            self.queryset = self.get_queryset().filter(created_by_id=user.id)
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="异步导出详情", extensions={"x-function": "ExportRetrieve", "x-assign_permission": False})
    def retrieve(self, request, *args, **kwargs):
        """
        获取单个导出任务的详细信息，包括状态、进度、文件地址等

        Args:
            request: 请求对象，kwargs 含任务主键

        Returns:
            统一成功响应（含任务详情）
        """
        response = super().retrieve(request, *args, **kwargs)
        return success_response(message="导出任务信息获取成功", data=response.data)

    def get_export_resource_kwargs(self):
        """
        为资源类提供额外的参数：
            - _selected_fields：自定义导出字段参数
            - _permitted_attrs：允许导出的字段 attribute 集合（字段级可下载权限过滤）
            - user_id / api_path / method / query_params：供资源类记录导出上下文

        字段权限规则（与同步导出 sync_export 保持一致）：
            - 未显式分配权限的字段默认拥有全部权限（可导出）；
            - 已显式分配的字段，仅当“非禁止访问且可下载”时才可导出。

        实现说明：
        在视图层（有 request.user）完成权限计算，Celery worker 中的资源类仅做字段过滤。

        Returns:
            传给资源类构造函数的 kwargs 字典
        """
        # 前端按 {params: 筛选条件, data: 导出选项} 提交；兼容旧版顶层参数。
        request_data = self.request.data
        export_options = request_data.get("data") or {}
        query_params = request_data.get("params") or self.request.query_params
        if hasattr(query_params, "dict"):
            query_params = query_params.dict()

        # 解析用户指定的导出字段（逗号分隔 → 列表，未传则导出全部字段）
        selected_fields = export_options.get(
            "selected_fields", request_data.get("selected_fields")
        )
        selected_fields = selected_fields.split(",") if selected_fields else None

        # 数据权限配置对应原列表 GET 接口，而不是异步任务的 start POST 接口。
        api_path = self.request.path
        async_start_suffix = "async_export/start/"
        if api_path.endswith(async_start_suffix):
            api_path = api_path[:-len(async_start_suffix)]

        # 根据当前用户的字段级权限，计算允许导出的字段 attribute 集合（None 表示不限制）
        permitted_attrs = _compute_permitted_export_attrs(
            resource_class=self.resource_class,
            user=self.request.user,
        )

        return {
            "_selected_fields": selected_fields,
            "_permitted_attrs": permitted_attrs,
            "user_id": self.request.user.id,
            "api_path": api_path,
            "query_params": query_params,
        }

    @require_celery_active
    def start_export(self, request):
        """
        创建一个导出任务并立即启动

        Args:
            request: 请求对象

        Returns:
            统一成功响应
        """
        response = super().start_export(request)
        return success_response(message="导出任务创建成功")

    @require_celery_active
    def cancel(self, *args, **kwargs):
        """
        取消正在进行的导出任务

        Returns:
            统一成功响应
        """
        response = super().cancel(*args, **kwargs)
        return success_response(message="导出任务取消成功")

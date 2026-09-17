#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：async_import_mixin.py
@Author  ：李小涛
@Date    ：2025/11/30 下午3:21 
@Explain : 通用异步导入视图（基于 django-import-export-extensions）
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from import_export_extensions.api import ImportJobViewSet, ImportJobSerializer
from import_export_extensions.models import ImportJob

from extends.drf.response import success_response
from extends.celery.celery_active import require_celery_active


class CustomImportJobSerializer(ImportJobSerializer):
    """
    异步导入任务序列化类：
    仅暴露前端需要的字段，减少响应数据传输量
    """

    class Meta:
        model = ImportJob
        fields = (
            "id",
            "created",
            "import_status",
            "import_params",
            "import_started",
            "import_finished",
            "input_errors_file",
            "error_message",
        )


class CustomImportJobViewSet(ImportJobViewSet):
    """
    自定义异步导入任务视图集：
        - 统一返回格式（success_response）
        - 非管理员只能查看自己的导入任务
        - 动态生成 Swagger 文档（x-function 扩展）
        - 资源类可获取当前用户信息（user_id / dept_id）
    """

    ordering = ("-id",)
    serializer_class = CustomImportJobSerializer
    import_open_api_description = (
        "该接口用于创建导入任务并立即启动。\n"
        "- 要监控任务进度，请使用任务的详情接口来获取任务状态。\n"
        "- 当状态变为 `PARSED` 时，你可以确认导入，数据将开始被导入系统。\n"
        "- 当状态为 `INPUT_ERROR` 或 `PARSE_ERROR` 时，表示数据未通过校验，无法导入。\n"
        "- 当状态为 `IMPORTED` 时，表示数据已成功导入系统，任务已完成。\n"
    )

    def __init_subclass__(cls) -> None:
        """
        子类创建时动态补充 OpenAPI 文档描述

        实现说明：
        start_import_action / cancel / confirm 等动作由父类 mixin 在运行时注入，
        无法通过静态装饰器添加 extend_schema，因此需在此处动态添加。
        """
        # 先让父类（包括 ImportStartActionMixin）完成初始化
        super().__init_subclass__()
        # === 动态添加 extend_schema ===
        schema_dict = {
            "start_import_action": extend_schema(
                summary="异步导入创建",
                extensions={"x-function": "ImportStart", "x-assign_permission": False},
                responses={201: cls.serializer_class},
            ),
            "cancel": extend_schema(
                summary="异步导入取消",
                extensions={"x-function": "ImportCancel", "x-assign_permission": False},
                responses={200: {}},
            ),
            "confirm": extend_schema(
                summary="异步导入确认",
                extensions={"x-function": "ImportConfirm", "x-assign_permission": False},
                responses={200: {}},
            ),
        }
        extend_schema_view(**schema_dict)(cls)

    @extend_schema(summary="异步导入列表", extensions={"x-function": "ImportList", "x-assign_permission": False})
    def list(self, request, *args, **kwargs):
        """
        异步导入任务列表：
            - 管理员：获取所有导入任务的分页列表
            - 普通用户：仅获取自己的导入任务列表

        Args:
            request: 请求对象

        Returns:
            分页列表响应
        """
        user = request.user
        if not user.is_superuser:
            self.queryset = self.get_queryset().filter(created_by_id=user.id)
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="异步导入详情", extensions={"x-function": "ImportRetrieve", "x-assign_permission": False})
    def retrieve(self, request, *args, **kwargs):
        """
        获取单个导入任务的详细信息，包括状态、进度、错误信息等

        Args:
            request: 请求对象，kwargs 含任务主键

        Returns:
            统一成功响应（含任务详情）
        """
        response = super().retrieve(request, *args, **kwargs)
        return success_response(message="导入任务信息获取成功", data=response.data)

    def get_import_resource_kwargs(self):
        """
        为导入资源类提供额外的参数：
            - user_id：当前用户 id（供资源类记录导入人）
            - dept_id：当前用户所属部门 id（供资源类记录数据归属部门）

        无 api_path/query_params，资源类自动跳过搜索与数据权限过滤。

        Returns:
            传给资源类构造函数的 kwargs 字典
        """
        user = self.request.user
        return {
            "user_id": user.id,
            "dept_id": getattr(user, "dept_id", None),
        }

    @require_celery_active
    def start_import(self, request):
        """
        创建一个导入任务并立即启动

        Args:
            request: 请求对象

        Returns:
            统一成功响应
        """
        response = super().start_import(request)
        return success_response(message="导入任务创建成功")

    @require_celery_active
    def cancel(self, *args, **kwargs):
        """
        取消正在进行的导入任务

        Returns:
            统一成功响应
        """
        response = super().cancel(*args, **kwargs)
        return success_response(message="导入任务取消成功")

    @require_celery_active
    def confirm(self, *args, **kwargs):
        """
        确认状态为 `PARSED` 的导入任务，开始执行实际导入

        Returns:
            统一成功响应
        """
        response = super().confirm(*args, **kwargs)
        return success_response(message="确认导入任务成功")

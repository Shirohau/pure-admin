#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：crud_mixin.py
@Author  ：李小涛
@Date    ：2025/11/27 上午11:57 
@Explain : 自定义 CrudViewSet：统一标准的增删改查视图
"""

import logging

from django.db.models.deletion import ProtectedError
from drf_spectacular.utils import extend_schema
from rest_framework.viewsets import ModelViewSet

from extends.drf.permissions import DataScopeFilter
from extends.drf.response import success_response, error_response

logger = logging.getLogger(__name__)


class CrudViewSet(ModelViewSet):
    """
    自定义的 ModelViewSet：统一标准的返回格式

    可配置属性：
        - create_serializer_class: 新增时使用的序列化类（默认 None，使用默认序列化类）
        - update_serializer_class: 更新时使用的序列化类（默认 None，使用默认序列化类）
        - search_fields: 模糊搜索字段列表（配合 list 接口的 ?search= 参数使用）
        - ordering_fields: 排序字段，默认为 "__all__"，表示允许按任意字段排序
        - filterset_class: 指定的筛选类（优先级高于自动生成的筛选器）
        - extra_filter_class: 额外的过滤器列表，默认包含 DataScopeFilter（数据权限过滤）
        - select_related: 默认需要关联查询的外键表，避免 N+1 查询
        - get_summary: 选填钩子，实现后 list 接口响应携带 summary 字段（表尾合计），入参为已筛选的查询集
    """

    http_method_names = ["get", "post", "put", "delete"]
    create_serializer_class = None
    update_serializer_class = None
    search_fields = []  # 模糊搜索字段
    ordering_fields = "__all__"  # 排序字段
    filterset_class = None  # 指定筛选类
    extra_filter_class = [DataScopeFilter]
    select_related = ["creator", "updater", "dept_belong"]  # 默认需要关联的外键表

    def filter_queryset(self, queryset):
        """
        过滤查询集：合并默认过滤器与自定义过滤器，并依次执行

        Args:
            queryset: 待过滤的查询集

        Returns:
            过滤后的查询集
        """
        # 合并所有过滤器类（默认 + 额外，set 去重）
        filter_classes = set(self.filter_backends) | set(self.extra_filter_class)
        # 实例化所有过滤器类
        backend_instances = [backend() for backend in filter_classes]
        # 依次执行每个过滤器的过滤逻辑
        for backend in backend_instances:
            queryset = backend.filter_queryset(self.request, queryset, self)
        return queryset

    def get_serializer_class(self):
        """
        获取序列化类：
        优先使用「动作对应的专用序列化类」（如 create_serializer_class），
        未配置时回退到视图默认的序列化类

        Returns:
            序列化类
        """
        action_serializer_class = getattr(self, f"{self.action}_serializer_class", None)
        return action_serializer_class or super().get_serializer_class()

    def get_queryset(self):
        """
        获取查询集，并预加载 select_related 指定的关联外键（优化查询性能）

        Returns:
            带关联预加载的查询集
        """
        return super().get_queryset().select_related(*self.select_related)

    def get_summary(self, queryset):
        """
        列表表尾合计：按当前筛选条件自定义合计（分页场景前端只有当前页，无法自行计算）
        Args:
            queryset: 已应用筛选条件的查询集
        Returns:
            dict: 列 property → 合计值（键需与前端列名一致，无数据时为 0）
        """
        return None

    @extend_schema(summary="列表", extensions={"x-function": "List"})
    def list(self, request, *args, **kwargs):
        """
        查询列表，扩展功能：
         - paginate：控制分页，默认启用 `paginate=true`，关闭分页 `paginate=false`
         - query：字段过滤 `query="{id, name,dept_name}"`
         - search：模糊搜索 `search=500G`，需要配置 search_fields
         - ordering：排序 `ordering=-price,create_dt`，需要配置 ordering_fields
         - 数据筛选：请参考 `backend/extends/drf/filters.py` 里面的约定
            - ?name__icontains=张          → queryset.filter(name__icontains='张')
            - ?birth_date__gte=2024-01-01  → queryset.filter(birth_date__gte='2024-01-01')
            - ?gender__in=男,女            → queryset.filter(gender__in=[男,女])
         - 父 => 子
            - ?author__name__icontains=张  → queryset.filter(author__name__icontains=张)
         - 子 => 父
            - ?author_books__id__exact=159  → queryset.filter(author_books__id__exact=159)
         - 表尾合计：视图实现 get_summary(queryset) 时响应携带 summary 字段，未实现为 null

        Args:
            request: 请求对象

        Returns:
            分页列表响应，或不分页的统一成功响应
        """
        queryset = self.filter_queryset(self.get_queryset())
        # 表尾合计：视图定义了 get_summary 时按其返回下发（如分页场景全量求和），未定义则为空（前端自行计算）
        summary = self.get_summary(queryset) if hasattr(self, "get_summary") else None
        # 默认启用分页，除非明确指定 paginate=false
        is_paginate = request.query_params.get("paginate", "true").lower() in ("true", "1", "yes")
        if not is_paginate:
            # 禁用分页：置空分页类，走不分页分支
            self.pagination_class = None
        page = self.paginate_queryset(queryset)
        if page is not None:
            # 分页分支：返回标准分页响应（含 count/next/previous/results）
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            # 不分页分支：返回统一格式的成功响应
            serializer = self.get_serializer(queryset, many=True)
            response = success_response(message="不分页列表查询成功", data=serializer.data)
        # 两个分支的响应体均为 success_response 的普通 dict，直接填充 summary 键
        response.data["summary"] = summary
        return response

    @extend_schema(summary="新增", extensions={"x-function": "Create"})
    def create(self, request, *args, **kwargs):
        """
        新增数据

        Args:
            request: 请求对象，body 为新增数据

        Returns:
            统一成功响应（含新增后的数据）
        """
        response = super().create(request, *args, **kwargs)
        return success_response(message="创建成功", data=response.data)

    @extend_schema(summary="详情", extensions={"x-function": "Retrieve"})
    def retrieve(self, request, *args, **kwargs):
        """
        查询详情

        Args:
            request: 请求对象，kwargs 含主键

        Returns:
            统一成功响应（含详情数据）
        """
        response = super().retrieve(request, *args, **kwargs)
        return success_response(message="查询详情成功", data=response.data)

    @extend_schema(summary="更新", extensions={"x-function": "Update"})
    def update(self, request, *args, **kwargs):
        """
        更新数据（强制走局部更新 partial=True，支持只传部分字段）

        Args:
            request: 请求对象，body 为待更新字段

        Returns:
            统一成功响应（含更新后的数据）
        """
        kwargs["partial"] = True
        response = super().update(request, *args, **kwargs)
        return success_response(message="更新成功", data=response.data)

    @extend_schema(summary="删除", extensions={"x-function": "Destroy"})
    def destroy(self, request, *args, **kwargs):
        """
        删除数据

        捕获 ProtectedError 异常：当数据被其他记录外键引用时，
        返回统一的错误响应而不是直接抛出 500。

        Args:
            request: 请求对象，kwargs 含主键

        Returns:
            删除成功响应，或被引用时的错误响应
        """
        try:
            super().destroy(request, *args, **kwargs)
        except ProtectedError as e:
            logger.warning("删除失败，存在受保护的外键引用: %s", e)
            return error_response(
                message="删除失败，该数据被其他记录引用，请先解除关联后再删除",
                data=str(e),
            )
        return success_response(message="删除成功")

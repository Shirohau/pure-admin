#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：views.py
@Author  ：李小涛
@Date    ：2025/11/26 下午5:34 
@Explain : 图书 视图
"""

from drf_spectacular.utils import extend_schema

from extends.drf.views_mixins import *

from .filters import BookFilter
from .models import BookModel
from .resources import BookResource
from .serializers import BookSerializer, BookCreateSerializer, BookUpdateSerializer


@extend_schema(tags=["图书"])
class BookViewSet(CrudViewSet, HistoryMixin, BatchDestroyMixin, ExportMixin, ImportMixin):
    """
    图书视图集

    N+1 查询优化：
        - select_related：预加载 publisher(publisher_name/publisher_updater_name/publisher_row)
          及其 updater(publisher_updater_name) + 审计字段(creator_name/updater_name/dept_belong_name)；
        - prefetch_related('author')：预加载多对多作者(author_all)内联序列化器；
        - 优化前（100 条记录）= 1(主表) + 100(publisher) + 100(publisher.updater) 
          + 100(author M2M) = 301 次查询；
        - 优化后 = 1(主表+JOINs) + 1(author prefetch) = 2 次查询。
    """

    queryset = BookModel.objects.all()

    # 预加载外键关联：publisher 及其 updater + 审计字段（creator/updater/dept_belong 由基类默认）
    select_related = ["creator", "updater", "dept_belong", "publisher", "publisher__updater"]

    search_fields = ["name", "description"]
    serializer_class = BookSerializer
    create_serializer_class = BookCreateSerializer
    update_serializer_class = BookUpdateSerializer
    filterset_class = BookFilter
    export_resource_class = BookResource  # 同步导入导出资源类
    import_resource_class = BookResource

    def get_queryset(self):
        """预加载多对多作者关联，避免内联 AuthorPartialSerializer 逐条查询。"""
        return super().get_queryset().prefetch_related('author')


@extend_schema(tags=["图书"])
class BookExportJobViewSet(CustomExportJobViewSet):
    resource_class = BookResource


@extend_schema(tags=["图书"])
class BookImportJobViewSet(CustomImportJobViewSet):
    resource_class = BookResource

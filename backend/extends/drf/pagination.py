#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：pagination.py
@Author  ：李小涛
@Date    ：2025/11/27 上午10:45 
@Explain : 自定义分页：支持 page/limit 参数与越界页码自动修正
"""

from django.core.paginator import EmptyPage, InvalidPage
from rest_framework.pagination import PageNumberPagination

from extends.drf.response import success_response

# 默认每页数量
DEFAULT_PAGE_SIZE = 10
# 每页最大数量（防止 limit 传超大值拖垮数据库）
MAX_PAGE_SIZE = 9999


class CustomPageNumberPagination(PageNumberPagination):
    """
    自定义分页类，使用 `page` 和 `limit` 参数。

    用法示例:
        - /api/books/                 -> 返回第一页，每页 DEFAULT_PAGE_SIZE 条
        - /api/books/?page=2          -> 返回第二页
        - /api/books/?limit=20        -> 返回第一页，每页20条
        - /api/books/?page=3&limit=15 -> 返回第三页，每页15条
    """

    page_size = DEFAULT_PAGE_SIZE          # 默认每页的数量
    max_page_size = MAX_PAGE_SIZE          # 每页最大的数量
    page_query_param = "page"              # 页码参数
    page_size_query_param = "limit"        # 每页数量参数

    def paginate_queryset(self, queryset, request, view=None):
        """
        对查询集进行分页处理；页码越界时自动修正为最后一页（或第一页）。

        与 DRF 默认行为差异：请求的页码超出范围时不报 404，
        而是回退到最后一页，避免数据删除后前端出现空页异常。

        Args:
            queryset: 待分页的查询集
            request: 请求对象
            view: 当前视图（默认 None，本实现未使用）

        Returns:
            list | None: 当前页数据列表；page_size 为 None（不需要分页）时返回 None
        """
        self.request = request
        page_size = self.get_page_size(request)
        # page_size 为 None 表示当前请求不需要分页（返回全量数据）
        if page_size is None:
            return None

        # 创建 Django 分页器并获取请求的页码
        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)

        try:
            self.page = paginator.page(page_number)
        except (InvalidPage, EmptyPage):
            # 页码越界处理：总页数为 0 时回退到第一页，否则回退到最后一页
            if paginator.num_pages == 0:
                self.page = paginator.page(1)
            else:
                self.page = paginator.page(paginator.num_pages)

        return list(self.page)

    def get_paginated_response(self, data):
        """
        重写分页响应：在统一成功响应中附加分页元数据。

        Args:
            data: 当前页的序列化数据

        Returns:
            Response: 统一格式响应，paginated 字段包含翻页链接与分页统计
        """
        return success_response(
            code=2000,
            message="分页列表查询成功",
            data=data,
            paginated={
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page": self.page.number,
                "limit": self.get_page_size(self.request),
                "total": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
            }
        )

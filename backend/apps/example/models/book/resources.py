#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：resources.py
@Author  ：李小涛
@Date    ：2026/8/3
@Explain : 图书导入导出资源（同步/异步通用）
"""
from import_export.fields import Field
from import_export.widgets import DateTimeWidget

from extends.drf.resources import CustomCeleryResource, CreatedManyToManyWidget, CreatedForeignKeyWidget
from .filters import BookFilter
from .models import BookModel
from ..author.models import AuthorModel
from ..publisher.models import PublisherModel


class BookResource(CustomCeleryResource):
    """图书导入导出资源（同步/异步通用）"""

    filterset_class = BookFilter

    publisher = Field(
        attribute="publisher",
        column_name="出版社",
        widget=CreatedForeignKeyWidget(
            PublisherModel,  # type: ignore[arg-type]
            field="name"
        ),
    )
    author = Field(
        attribute="author",
        column_name="作者",
        widget=CreatedManyToManyWidget(
            AuthorModel,  # type: ignore[arg-type]
            field="name",
            separator="|"
        ),
    )
    name = Field(attribute="name", column_name="书名")
    isbn = Field(attribute="isbn", column_name="ISBN")
    publication_time = Field(
        attribute="publication_time",
        column_name="出版时间",
        widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S'),
    )
    price = Field(attribute="price", column_name="价格")
    pages = Field(attribute="pages", column_name="页数")
    description = Field(attribute="description", column_name="内容简介")

    class Meta:
        model = BookModel
        fields = (
            "publisher", "author",
            "name", "isbn", "publication_time",
            "price", "pages", "description"
        )
        import_id_fields = ["isbn"]
        use_bulk = False
        batch_size = 100
        skip_unchanged = True

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：resources.py
@Author  ：李小涛
@Date    ：2026/8/3
@Explain : 作者导入导出资源（同步/异步通用）
"""
from import_export.fields import Field

from extends.drf.resources import CustomCeleryResource
from .filters import AuthorFilter
from .models import AuthorModel


class AuthorResource(CustomCeleryResource):
    """作者导入导出资源（同步/异步通用）"""

    filterset_class = AuthorFilter
    search_fields = ["name", "biography"]

    name = Field(attribute='name', column_name="作者姓名")
    gender = Field(attribute='gender', column_name="性别")
    age = Field(attribute='age', column_name="年龄")
    birth_date = Field(attribute='birth_date', column_name="出生日期")
    biography = Field(attribute='biography', column_name="简介")

    # 导入模板列宽配置（xlsx 格式生效）
    import_column_widths = {
        "作者姓名": 15,
        "性别": 8,
        "年龄": 8,
        "出生日期": 15,
        "简介": 40,
    }

    class Meta:
        model = AuthorModel
        fields = ('name', 'gender', 'age', 'birth_date', 'biography')
        import_id_fields = ['name']
        use_bulk = False
        batch_size = 100
        skip_unchanged = True

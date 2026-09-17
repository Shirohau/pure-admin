#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：resources.py
@Author  ：李小涛
@Date    ：2026/8/3
@Explain : 菜单字段导入导出资源（同步/异步通用）
"""
from import_export.fields import Field

from extends.drf.resources import CustomCeleryResource
from .filters import MenuFieldFilter
from .models import MenuFieldModel


class MenuFieldResource(CustomCeleryResource):
    """菜单字段导入导出资源（同步/异步通用）"""

    filterset_class = MenuFieldFilter
    menu = Field(attribute='menu__title', column_name="关联菜单")

    class Meta:
        model = MenuFieldModel
        fields = (
            'id',
            'menu',
            'model',
            'field_name',
            'verbose_name',
        )

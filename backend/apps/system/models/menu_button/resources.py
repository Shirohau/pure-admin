#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：resources.py
@Author  ：李小涛
@Date    ：2026/8/3
@Explain : 菜单按钮导入导出资源（同步/异步通用）
"""
from import_export.fields import Field

from extends.drf.resources import CustomCeleryResource
from .filters import MenuButtonFilter
from .models import MenuButtonModel


class MenuButtonResource(CustomCeleryResource):
    """菜单按钮导入导出资源（同步/异步通用）"""

    filterset_class = MenuButtonFilter

    menu = Field(attribute='menu__title', column_name="关联菜单")

    class Meta:
        model = MenuButtonModel
        fields = (
            'id',
            'menu',
            'name',
            'key',
            'api',
            'method',
        )

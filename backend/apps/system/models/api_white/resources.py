#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：resources.py
@Author  ：李小涛
@Date    ：2026/8/3
@Explain : 接口白名单导入导出资源（同步/异步通用）
"""
from import_export.fields import Field

from extends.drf.resources import CustomCeleryResource
from .filters import ApiWhiteFilter
from .models import ApiWhiteModel


class ApiWhiteResource(CustomCeleryResource):
    """接口白名单导入导出资源（同步/异步通用）"""

    filterset_class = ApiWhiteFilter
    name = Field(attribute='name', column_name="描述")
    api = Field(attribute='api', column_name="地址")
    method = Field(attribute='method', column_name="请求方法")
    status = Field(attribute='status', column_name="状态")

    class Meta:
        model = ApiWhiteModel
        fields = ('name', 'api', 'method', 'status')
        import_id_fields = ('api',)

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：resources.py
@Author  ：李小涛
@Date    ：2026/8/3
@Explain : 配置导入导出资源（同步/异步通用）
"""
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget, JSONWidget, CharWidget

from extends.drf.resources import CustomCeleryResource
from .filters import ConfigFilter
from .models import ConfigModel


class ConfigResource(CustomCeleryResource):
    """配置导入导出资源（同步/异步通用）"""

    filterset_class = ConfigFilter
    parent_key = Field(
        attribute='parent',
        column_name="父级编码",
        widget=ForeignKeyWidget(ConfigModel, field='key'),
    )
    title = Field(attribute='title', column_name="标题")
    key = Field(attribute='key', column_name="键")
    form_type = Field(attribute='form_type', column_name="表单类型")
    value = Field(attribute='value', column_name="内容", widget=JSONWidget())
    setting = Field(attribute='setting', column_name="配置", widget=JSONWidget())
    closable = Field(attribute='closable', column_name="是否可关闭")

    class Meta:
        model = ConfigModel
        fields = ('parent_key', 'title', 'key', 'form_type', 'value', 'setting', 'closable')
        import_id_fields = ('key',)

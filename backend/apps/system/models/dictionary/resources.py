#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：resources.py
@Author  ：李小涛
@Date    ：2026/8/3
@Explain : 字典导入导出资源（同步/异步通用）
"""
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget, CharWidget

from extends.drf.resources import CustomCeleryResource
from .filters import DictionaryFilter
from .models import DictionaryModel


class DictionaryResource(CustomCeleryResource):
    """字典导入导出资源（同步/异步通用）

    当 coerce_to_string 为 True 时，调用 Widget.render() 返回字符串形式；
    当 coerce_to_string 为 False 时，直接返回值本身（不转换为字符串）。
    """

    filterset_class = DictionaryFilter
    parent_value = Field(
        attribute='parent',
        column_name="父级值",
        widget=ForeignKeyWidget(DictionaryModel, field='value'),
    )
    label = Field(attribute='label', column_name="名称")
    value = Field(attribute='value', column_name="值")
    color = Field(attribute='color', column_name="颜色", widget=CharWidget(coerce_to_string=False))
    level = Field(attribute='level', column_name="层级", widget=CharWidget(coerce_to_string=False))
    status = Field(attribute='status', column_name="状态", widget=CharWidget(coerce_to_string=False))
    remark = Field(attribute='remark', column_name="备注")

    class Meta:
        model = DictionaryModel
        fields = ('parent_value', 'label', 'value', 'color', 'level', 'status', 'remark')
        import_id_fields = ('value',)

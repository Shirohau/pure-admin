#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：models.py
@Explain : 流程信息模型（AntFlow-Designer 设计器数据契约字段）
"""

from django.db import models

from ...models import table_prefix
from extends.drf.models import CustomModel


class FlowInfoModel(CustomModel):
    """流程信息"""
    name = models.CharField(max_length=50, verbose_name='流程名称')
    icon = models.JSONField(blank=True, default=dict, verbose_name='图标')
    form_conf = models.JSONField(blank=True, default=dict, verbose_name='form配置')

    class Meta:
        db_table = table_prefix + 'info'
        verbose_name = '流程管理'
        verbose_name_plural = verbose_name
        ordering = ('-id',)

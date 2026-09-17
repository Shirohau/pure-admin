#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2026/3/16 下午2:58 
@Explain : 字典管理
"""

from django.db import models

from extends.drf.models import CustomSortModel
from apps.system.models import table_prefix


class DictionaryModel(CustomSortModel):
    parent = models.ForeignKey(
        to="self",
        related_name="children",
        db_constraint=False,
        on_delete=models.PROTECT,  # 保护删除
        blank=True,
        null=True,
        verbose_name="父级",
        db_comment="父级",
    )
    label = models.CharField(max_length=100, verbose_name="名称", db_comment="名称")
    value = models.CharField(max_length=200, unique=True, verbose_name="值", db_comment="值")
    color = models.CharField(max_length=20, blank=True, null=True, verbose_name="颜色", db_comment="颜色")
    level = models.BigIntegerField(verbose_name="层级", db_comment="层级")
    status = models.BooleanField(default=True, verbose_name="状态", db_comment="状态")
    remark = models.TextField(blank=True, null=True, verbose_name="备注", db_comment="备注")

    class Meta:
        db_table = table_prefix + "dictionary"
        verbose_name = "字典表"
        verbose_name_plural = verbose_name
        ordering = ("sort",)

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2026/2/26 下午4:45 
@Explain : 系统配置表
"""
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from extends.drf.models import CustomSortModel
from apps.system.models import table_prefix


class ConfigModel(CustomSortModel):
    parent = models.ForeignKey(
        to="self",
        verbose_name="父级",
        on_delete=models.PROTECT,
        db_constraint=False,
        null=True,
        blank=True,
        db_comment="父级",
    )
    title = models.CharField(max_length=50, verbose_name="标题", db_comment="标题")
    key = models.CharField(max_length=100, verbose_name="键", db_comment="键", unique=True)
    form_type = models.CharField(max_length=100, verbose_name="表单类型", db_comment="表单类型", null=True, blank=True)
    value = models.JSONField(max_length=100, verbose_name="内容", db_comment="内容", null=True, blank=True)
    setting = models.JSONField(verbose_name="配置", db_comment="配置", null=True, blank=True)
    closable = models.BooleanField(default=True, verbose_name="是否可关闭", db_comment="是否可关闭")
    image = GenericRelation(to="system.FileModel", related_query_name='image')  # 反向查询名

    class Meta:
        db_table = table_prefix + "config"
        verbose_name = "系统配置表"
        verbose_name_plural = verbose_name
        ordering = ("sort",)

    def __str__(self):
        return f"{self.title}"

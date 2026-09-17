#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2025/12/21 下午4:57 
@Explain : 角色表
"""
from django.db import models
from apps.system.models import table_prefix
from extends.drf.models import CustomSortModel


class RoleModel(CustomSortModel):
    name = models.CharField(max_length=64, verbose_name="名称", db_comment="名称")
    code = models.CharField(max_length=64, unique=True, verbose_name="编号", db_comment="编号")
    status = models.BooleanField(default=True, null=True, blank=True, verbose_name="状态", db_comment="状态")

    def __str__(self):
        return self.name

    class Meta:
        db_table = table_prefix + "role"
        verbose_name = "角色"
        verbose_name_plural = verbose_name
        db_table_comment = verbose_name
        ordering = ["sort"]

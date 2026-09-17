#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2026/2/3 下午3:40 
@Explain : 接口白名单
"""

from django.db import models

from extends.drf.models import CustomModel
from apps.system.models import table_prefix


class ApiWhiteModel(CustomModel):
    name = models.CharField(max_length=64, verbose_name="描述", db_comment="描述")
    api = models.CharField(max_length=200, unique=True, verbose_name="地址", db_comment="地址")
    method = models.CharField(max_length=10, verbose_name="请求方法", db_comment="请求方法")
    status = models.BooleanField(default=True, verbose_name="状态", help_text="状态", blank=True)

    class Meta:
        db_table = table_prefix + "api_white"
        verbose_name = "接口白名单"
        verbose_name_plural = verbose_name
        ordering = ("-create_dt",)

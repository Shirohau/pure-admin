#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：models.py
@Author  ：李小涛
@Date    ：2025/11/26 下午5:20
@Explain : 作者 数据表
"""

from django.db import models
from simple_history.models import HistoricalRecords

from apps.example.models import table_prefix
from extends.drf.models import CustomModel


class AuthorModel(CustomModel):
    name = models.CharField(verbose_name="作者姓名", db_comment="作者姓名", max_length=64)
    gender = models.CharField(verbose_name="性别", db_comment="性别", max_length=1, blank=True, null=True)
    birth_date = models.DateField(verbose_name="出生日期", db_comment="出生日期", blank=True, null=True)
    age = models.IntegerField(verbose_name="年龄", db_comment="年龄", blank=True, null=True)
    education = models.CharField(verbose_name="学历", db_comment="学历", max_length=50, blank=True, null=True)
    province = models.CharField(verbose_name="省份", db_comment="省份", max_length=50, blank=True, null=True)
    city = models.CharField(verbose_name="城市", db_comment="城市", max_length=50, blank=True, null=True)
    district = models.CharField(verbose_name="区县", db_comment="区县", max_length=50, blank=True, null=True)
    address = models.CharField(verbose_name="详细地址", db_comment="详细地址", max_length=255, blank=True, null=True)
    biography = models.TextField(verbose_name="简介", db_comment="简介", blank=True, null=True)

    # 历史记录
    history = HistoricalRecords(table_name=table_prefix + 'author_history', verbose_name="作者 历史记录")

    def __str__(self):
        return self.name

    class Meta:
        db_table = table_prefix + "author"
        verbose_name = "作者"
        db_table_comment = verbose_name
        verbose_name_plural = verbose_name
        ordering = ['-id']

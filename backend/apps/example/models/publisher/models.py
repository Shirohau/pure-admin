#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2025/11/26 下午3:08 
@Explain : 出版社 数据表
"""

from django.db import models
from simple_history.models import HistoricalRecords

from apps.example.models import table_prefix
from extends.drf.models import CustomModel


class PublisherModel(CustomModel):
    name = models.CharField(verbose_name="出版社名称", db_comment="出版社名称", max_length=255, unique=True)
    province = models.CharField(verbose_name="省份", db_comment="省份", max_length=255)
    city = models.CharField(verbose_name="城市", db_comment="城市", max_length=255)
    district = models.CharField(verbose_name="区县", db_comment="区县", max_length=255)
    address = models.CharField(verbose_name="详细地址", db_comment="详细地址", max_length=255)
    phone = models.CharField(verbose_name="联系电话", db_comment="联系电话", max_length=20, blank=True, null=True)
    email = models.EmailField(verbose_name="邮箱", db_comment="邮箱", blank=True, null=True)
    website = models.URLField(verbose_name="官网网址", db_comment="官网网址", blank=True, null=True)

    # 历史记录
    history = HistoricalRecords(table_name=table_prefix + 'publisher_history', verbose_name="出版社 历史记录")

    def area_str(self):
        return " / ".join([self.province, self.city, self.district])

    def __str__(self):
        return self.name

    class Meta:
        db_table = table_prefix + "publisher"
        verbose_name = "出版社"
        db_table_comment = verbose_name
        verbose_name_plural = verbose_name
        ordering = ['-id']

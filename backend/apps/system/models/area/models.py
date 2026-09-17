#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2026/2/27 上午8:53 
@Explain : 地区管理
"""
from django.db import models
from pypinyin import lazy_pinyin
from pypinyin.constants import Style

from extends.drf.models import CustomModel
from apps.system.models import table_prefix


def get_pinyin(name: str):
    """根据中文名称生成拼音和首字母"""
    if not name:
        return "", ""
    # 获取带声调的拼音（不带声调）
    pinyin_list = lazy_pinyin(name, style=Style.NORMAL, errors='ignore')
    pinyin = ''.join(pinyin_list).lower()
    initials = ''.join([p[0] for p in pinyin_list if p]).upper()
    return pinyin, initials


class AreaModel(CustomModel):
    name = models.CharField(max_length=100, verbose_name="名称", db_comment="名称")
    code = models.CharField(max_length=20, verbose_name="地区编码", db_comment="地区编码", unique=True, db_index=True)
    level = models.BigIntegerField(verbose_name="地区层级(1省份 2城市 3区县 4乡级)", db_comment="地区层级(1省份 2城市 3区县 4乡级)")
    pinyin = models.CharField(max_length=255, verbose_name="拼音", null=True, blank=True, db_comment="拼音")
    initials = models.CharField(max_length=255, verbose_name="首字母", null=True, blank=True, db_comment="首字母")
    enable = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")
    parent = models.ForeignKey(
        to="self",
        related_name="children",
        db_constraint=False,
        on_delete=models.CASCADE,  # 级联删除
        blank=True,
        null=True,
        verbose_name="父地区编码",
        db_comment="父地区编码",
    )

    class Meta:
        db_table = table_prefix + "area"
        verbose_name = "地区管理"
        verbose_name_plural = verbose_name
        ordering = ("code",)

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.pinyin, self.initials = get_pinyin(self.name)
        super().save(*args, **kwargs)

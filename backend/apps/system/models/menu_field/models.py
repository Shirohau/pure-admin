#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2025/11/14 下午9:49 
@Explain :
"""

from django.db import models

from apps.system.models import table_prefix
from extends.drf.models import CustomSortModel


class MenuFieldModel(CustomSortModel):
    menu = models.ForeignKey(
        to="MenuModel",
        related_name="menu_field",
        verbose_name="关联菜单",
        db_comment="关联菜单",
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    model = models.CharField(max_length=64, db_index=True, verbose_name='模型表', db_comment="模型表")
    field_name = models.CharField(max_length=64, verbose_name='字段名', db_comment="字段名")
    verbose_name = models.CharField(max_length=64, verbose_name='字段显示名', db_comment="字段显示名")

    class Meta:
        db_table = table_prefix + "menu_field"
        verbose_name = "菜单字段"
        verbose_name_plural = verbose_name
        db_table_comment = verbose_name
        ordering = ("id",)
        # ✅ 联合唯一约束：menu + model + field_name 组合必须唯一
        constraints = [
            models.UniqueConstraint(
                fields=['menu', 'model', 'field_name'],
                name='unique_menu_model_field_name'
            )
        ]

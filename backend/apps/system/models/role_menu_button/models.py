#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2026/1/10 下午2:18 
@Explain : 角色菜单按钮
"""

from django.db import models
from apps.system.models import table_prefix
from extends.drf.models import CustomSortModel


class RoleMenuButtonModel(CustomSortModel):
    role = models.ForeignKey(
        to="RoleModel",
        related_name="role_menu_button",
        on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="关联角色",
        db_comment="关联角色",
    )
    menu_button = models.ForeignKey(
        to="MenuButtonModel",
        related_name="role_menu_button",
        on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="关联菜单按钮",
        db_comment="关联菜单按钮"
    )
    DATASCOPE_CHOICES = (
        (0, "仅本人"),
        (1, "本部门"),
        (2, "本部门及以下"),
        (3, "自定义部门"),
        (4, "全部"),
    )
    permission_range = models.IntegerField(default=0, choices=DATASCOPE_CHOICES, verbose_name="权限范围", db_comment="权限范围")
    dept = models.ManyToManyField(to="DeptModel", blank=True, related_name="role_menu_button", verbose_name="数据权限-关联部门")

    class Meta:
        db_table = table_prefix + "role_menu_button"
        verbose_name = "角色菜单按钮"
        verbose_name_plural = verbose_name
        db_table_comment = verbose_name
        ordering = ("sort",)
        # ✅ 联合唯一约束：role + menu_button 组合必须唯一
        constraints = [
            models.UniqueConstraint(
                fields=['role', 'menu_button'],
                name='unique_role_menu_button'
            )
        ]

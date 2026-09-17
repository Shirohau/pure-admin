#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2026/1/14 下午4:06 
@Explain : 角色菜单字段
"""

from django.db import models
from apps.system.models import table_prefix
from extends.drf.models import CustomSortModel

# 数据权限等级常量（供视图层复用，与 DataPermission.choices 保持一致）
PERMISSION_LEVEL_DENIED = 0  # 禁止访问
PERMISSION_LEVEL_READ = 1  # 只读
PERMISSION_LEVEL_WRITE = 2  # 可读写

# 功能权限目录：key -> 显示名
# ★ 可配置扩展点：新增功能权限时只需在此追加一项，即可自动生效于：
#   - 后端 func_permission_definitions 接口返回（前端面板据此动态渲染列与勾选交互）；
#   - 保存/校验白名单（_validate_func_permissions 仅接受此处声明的 key）；
#   - 角色导入导出（resources.py 按此动态生成"是否xxx"列）；
#   - 页面字段权限合并（menu/views.py page_perms 按此动态合并返回）；
#   - 导出/下载链路校验（sync_export_mixin 的 EXPORT_FUNC_PERMISSION_KEYS 引用）
FUNC_PERMISSION_DEFINITIONS = {
    "can_download": "可下载",
    # "can_print": "可打印",
}


class RoleMenuFieldModel(CustomSortModel):
    """角色菜单字段：记录某个角色在某个菜单字段上的权限分配。

    权限语义：
    - 未分配记录（无 RoleMenuFieldModel 行）＝ 默认拥有全部权限（数据可读写 + 全部功能权限）；
    - 一旦分配记录，则仅拥有被分配的权限（permission_level 数据权限等级 + func_permissions 功能权限组合）；
    - 数据权限等级与功能权限完全独立：仅分配功能权限时 permission_level 为 NULL（不默认任何等级），
      仅分配数据等级时 func_permissions 保持未分配状态，两者互不联动。

    记录生命周期：
    - 创建时机：仅在分配权限的那一刻落库（单条勾选或批量授权时 upsert）；
    - 取消全部权限：删除记录，回到“默认拥有全部权限”语义；
    - 唯一性：role + menu_field 组合唯一，记录存在则更新、不存在则创建。
    """
    role = models.ForeignKey(
        to="RoleModel",
        related_name="role_menu_field",
        on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="关联角色",
        db_comment="关联角色",
    )
    menu_field = models.ForeignKey(
        to="MenuFieldModel",
        related_name="role_menu_field",
        on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="关联菜单字段",
        db_comment="关联菜单字段"
    )

    class DataPermission(models.IntegerChoices):
        DENY = 0, "禁止访问"
        READ_ONLY = 1, "只读"
        READ_WRITE = 2, "可读写"

    permission_level = models.IntegerField(
        null=True, blank=True, default=None, choices=DataPermission.choices,
        verbose_name="数据权限等级",
        db_comment="数据权限等级：0=禁止访问 1=只读 2=可读写；NULL=未显式分配（与功能权限完全独立）",
    )
    # ✅ 功能权限容器（JSON）：{功能权限key: bool}，key 见 FUNC_PERMISSION_DEFINITIONS
    func_permissions = models.JSONField(
        default=dict, blank=True,
        verbose_name="功能权限集",
        db_comment='功能权限集，如 {"can_download": true, "can_print": true}，key 见 FUNC_PERMISSION_DEFINITIONS',
    )

    class Meta:
        db_table = table_prefix + "role_menu_field"
        verbose_name = "角色菜单字段"
        verbose_name_plural = verbose_name
        db_table_comment = verbose_name
        ordering = ("sort",)
        # ✅ 联合唯一约束：role + menu_field 组合必须唯一
        constraints = [
            models.UniqueConstraint(
                fields=['role', 'menu_field'],
                name='unique_role_menu_field'
            )
        ]

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：permissions.py
@Author  ：李小涛
@Date    ：2026/2/9 下午4:48 
@Explain : 数据级权限过滤器（行级权限）
"""

import re

from rest_framework.filters import BaseFilterBackend

from apps.system.models.api_white.models import ApiWhiteModel
from apps.system.models.dept.models import DeptModel
from apps.system.models.role_menu_button.models import RoleMenuButtonModel

# ===========================================================================
# 权限等级常量（对应 RoleMenuButtonModel.permission_range 字段值）
# ===========================================================================
PERMISSION_ONLY_SELF = 0            # 仅本人数据权限
PERMISSION_DEPT = 1                 # 本部门数据权限
PERMISSION_DEPT_AND_CHILDREN = 2    # 本部门及以下数据权限
PERMISSION_CUSTOM_DEPT = 3          # 自定义数据权限（关联部门）
PERMISSION_ALL = 4                  # 全部数据权限（最大权限）


class DataScopeFilter(BaseFilterBackend):
    """
    数据级权限过滤器（行级权限）

    权限等级：
        0: 仅本人数据权限
        1: 本部门数据权限
        2: 本部门及以下数据权限
        3: 自定义数据权限（关联部门）
        4: 全部数据权限（最大权限）

    规则：
        - 超级管理员直接放行；
        - 命中接口白名单的请求直接放行；
        - 模型无 dept_belong_id 字段 → 不过滤；
        - 多角色取最大权限：只要有一个角色 permission_range == 4 → 返回全部。

    权限优先级：
        4（全部） > 0（仅本人） > 1/2/3（部门类权限）
        一旦存在 0 且无 4，则强制限制为"仅本人"，忽略其他部门类权限，
        防止因多角色配置错误导致数据越权访问。
    """

    # 可通过子类覆盖这些字段名
    DEPT_BELONG_FIELD = "dept_belong_id"
    CREATOR_FIELD = "creator_id"

    def filter_queryset(self, request, queryset, view):
        """
        过滤器主入口：按顺序执行放行检查与权限过滤。

        Args:
            request: 请求对象
            queryset: 原始查询集
            view: 当前视图（本过滤器不需要，保留以兼容父类协议）

        Returns:
            QuerySet: 过滤后的查询集
        """
        # 1. 接口白名单：命中则不过滤
        if self._is_api_whitelisted(request):
            return queryset

        # 2. 超级管理员放行
        if getattr(request.user, "is_superuser", False):
            return queryset

        # 3. 执行权限范围过滤
        return self._apply_permission_range(request, queryset)

    @staticmethod
    def _is_api_whitelisted(request) -> bool:
        """
        检查当前请求 (path + method) 是否命中接口白名单（status=True）

        支持 {id} 通配符，例如：
            白名单 api: "/api/user/{id}/"
            匹配路径: "/api/user/123/", "/api/user/456/"

        Args:
            request: 请求对象

        Returns:
            bool: True 表示命中白名单（无需数据权限过滤）
        """
        request_path = request.path
        method = request.method
        # 查询当前方法下所有启用的白名单规则
        white_rules = ApiWhiteModel.objects.filter(status=True, method__iexact=method).only("api")
        for rule in white_rules:
            # 将 {id} 通配符转为数字正则，其余字符转义后整体匹配
            pattern = re.escape(rule.api)
            pattern = pattern.replace(r"\{id\}", r"\d+")
            pattern = f"^{pattern}$"
            if re.match(pattern, request_path):
                return True
        return False

    def _apply_permission_range(self, request, queryset):
        """
        根据用户的角色权限范围过滤查询集（核心过滤逻辑）

        Args:
            request: 请求对象
            queryset: 原始查询集

        Returns:
            QuerySet: 按权限过滤后的查询集
        """
        model = queryset.model
        user = request.user

        # 标准化 API 路径（/api/user/123/ → /api/user/{id}/）用于匹配权限规则
        api = self._normalize_api_path(request)

        # 情况 1: 模型不支持部门字段 → 不过滤
        if not hasattr(model, self.DEPT_BELONG_FIELD):
            return queryset

        # 情况 2: 用户没有分配部门 → 仅本人数据
        user_dept_id = getattr(user, "dept_id", None)
        if not user_dept_id:
            return queryset.filter(**{self.CREATOR_FIELD: user.id})

        # 情况 3: 用户没有分配有效角色 → 仅本人数据
        role_ids = list(user.role.filter(status=1).values_list("id", flat=True))
        if not role_ids:
            return queryset.filter(**{self.CREATOR_FIELD: user.id})

        # 查询用户所有角色在当前 API + 方法下的权限范围集合
        permission_ranges = set(
            RoleMenuButtonModel.objects.filter(
                role_id__in=role_ids,
                menu_button__api=api,
                menu_button__method=request.method,
                role__status=1,
            ).values_list("permission_range", flat=True)
        )

        # 情况 4: 有角色但未配置任何权限规则 → 仅本人数据
        if not permission_ranges:
            return queryset.filter(**{self.CREATOR_FIELD: user.id})

        # === 权限判断（按优先级）===
        # 存在"全部数据权限"(4) → 直接返回全部
        if PERMISSION_ALL in permission_ranges:
            return queryset

        # 存在"仅本人数据权限"(0) → 只看自己创建的数据
        if PERMISSION_ONLY_SELF in permission_ranges:
            return queryset.filter(**{self.CREATOR_FIELD: user.id})

        # 合并部门类权限的部门 ID 集合：
        #   1 本部门 / 2 本部门及以下 / 3 自定义关联部门
        dept_ids = set()
        if PERMISSION_DEPT in permission_ranges:
            dept_ids.add(user_dept_id)

        if PERMISSION_DEPT_AND_CHILDREN in permission_ranges:
            dept_ids.update(self._get_dept_children_ids(user_dept_id))

        if PERMISSION_CUSTOM_DEPT in permission_ranges:
            custom_dept_ids = RoleMenuButtonModel.objects.filter(
                role_id__in=role_ids,
                menu_button__api=api,
                menu_button__method=request.method,
                permission_range=PERMISSION_CUSTOM_DEPT,
                role__status=1,
            ).values_list("dept__id", flat=True)
            dept_ids.update(custom_dept_ids)

        # 部门 ID 为空（如自定义部门未配置）→ 返回空结果集，杜绝越权
        if not dept_ids:
            return queryset.none()

        # 特殊处理：查询的本身就是部门模型 → 直接按部门 ID 过滤
        if model._meta.model_name == "dept":
            return queryset.filter(id__in=dept_ids)
        return queryset.filter(**{f"{self.DEPT_BELONG_FIELD}__in": dept_ids})

    @staticmethod
    def _normalize_api_path(request):
        """
        将 /api/xxx/123/ 转为 /api/xxx/{id}/ 用于匹配权限规则

        Args:
            request: 请求对象

        Returns:
            str: 标准化后的 API 路径
        """
        api = request.path
        # 从 parser_context 中安全获取路径参数（该上下文由 DRF 注入）
        parser_context = getattr(request, "parser_context", None) or {}
        pk = (parser_context.get("kwargs") or {}).get("pk")
        if pk and str(pk).isdigit():
            # 仅替换路径中匹配的 pk 数字段，避免误替换其他数字段
            api = api.replace(f"/{pk}/", "/{id}/")
        return api

    @staticmethod
    def _get_dept_children_ids(dept_id):
        """
        获取指定部门及其所有子部门 ID（利用 MP_Node 的 children_ids）

        Args:
            dept_id: 部门 ID

        Returns:
            list[int]: 部门自身 + 所有后代部门 ID；部门不存在时返回空列表
        """
        try:
            dept = DeptModel.objects.get(id=dept_id)
            return dept.children_ids()  # 已包含自身 + 所有后代
        except DeptModel.DoesNotExist:
            return []

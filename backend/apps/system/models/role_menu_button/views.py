#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：views.py
@Author  ：李小涛
@Date    ：2026/1/10 下午2:18
@Explain : 角色菜单按钮 - 视图
"""
from django.db import transaction
from django.db.models import OuterRef, Subquery
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import error_response, success_response
from extends.drf.views_mixins import *

from .filters import RoleMenuButtonFilter
from .models import RoleMenuButtonModel
from .serializers import (
    RoleMenuButtonSerializer,
    RoleMenuButtonCreateSerializer,
    RoleMenuButtonUpdateSerializer,
)
from ..menu_button.models import MenuButtonModel
from ..role.models import RoleModel

# 数据权限范围：自定义部门（值为 3 时需携带关联部门列表）
PERMISSION_RANGE_CUSTOM_DEPT = 3


@extend_schema(tags=["角色菜单按钮"])
class RoleMenuButtonViewSet(CrudViewSet, BatchDestroyMixin):
    """
    角色菜单按钮视图集

    标准 CRUD 之外的自定义接口：
    - button_roles（GET /button_roles/）：按钮维度查询所有角色的授权情况，供"通过按钮授权角色"页面使用
    - roles_button（GET /roles_button/）：角色维度查询某菜单下所有按钮的授权情况，供"通过角色授权按钮"页面使用
    - batch_update（POST /batch_update/）：统一设置模式批量更新按钮权限范围，供授权按钮面板"统一设置"使用
    - batch_permission（POST /batch_permission/）：表头批量开启/关闭按钮权限，单次请求完成全量授权或取消
    - batch_button_permission（POST /batch_button_permission/）：表头批量开启/关闭角色权限，单次请求完成全量授权或取消
    - batch_button_update（POST /batch_button_update/）：统一设置模式批量更新角色权限范围，供通过按钮授权角色面板"统一设置"使用
    """

    queryset = RoleMenuButtonModel.objects.all().select_related("role", "menu_button")
    serializer_class = RoleMenuButtonSerializer
    create_serializer_class = RoleMenuButtonCreateSerializer
    update_serializer_class = RoleMenuButtonUpdateSerializer
    filterset_class = RoleMenuButtonFilter
    extra_filter_class = []

    @staticmethod
    def _get_dept_map(role_menu_button_ids):
        """
        批量获取权限记录关联的部门 ID 映射
        :param role_menu_button_ids: RoleMenuButtonModel 主键 ID 列表
        :return: { 记录ID: [部门ID, ...] }，无记录时返回空字典
        :description: 供 button_roles / roles_button 组装结果时复用，
        一次查询多对多中间表，避免逐条查询造成的 N+1 问题
        """
        dept_map = {}
        if not role_menu_button_ids:
            return dept_map
        dept_relations = RoleMenuButtonModel.dept.through.objects.filter(
            rolemenubuttonmodel_id__in=role_menu_button_ids
        ).values("rolemenubuttonmodel_id", "deptmodel_id")
        for relation in dept_relations:
            record_id = relation["rolemenubuttonmodel_id"]
            dept_id = relation["deptmodel_id"]
            dept_map.setdefault(record_id, []).append(dept_id)
        return dept_map

    @extend_schema(summary="通过按钮授权角色", extensions={"x-function": "ButtonRoles"})
    @action(methods=["GET"], detail=False)
    def button_roles(self, request, *args, **kwargs):
        """
        按钮维度：查询所有角色对该按钮的授权情况
        :param menu_button_id: 菜单按钮 ID（query 参数，必传）
        :return: 分页结果，每项包含 role / role_name / menu_button / need_data_scope /
                 role_menu_button / has_permission / permission_range / dept
        :description: 前端配合：通过按钮授权角色页面，用于展示“哪些角色拥有该按钮权限”。
        实现思路：先查出所有角色，再用子查询左连接标注每个角色是否已分配该按钮权限，
        最后批量补充关联部门 ID 列表
        """
        menu_button_id = request.query_params.get("menu_button_id")

        # 0. 查询按钮属性：是否需要数据访问（供前端判断是否渲染范围选择列）
        need_data_scope = (
            MenuButtonModel.objects.filter(pk=menu_button_id)
            .values_list("need_data_scope", flat=True)
            .first()
        )

        # 1. 子查询：查找每个角色在该按钮上的权限记录（记录 ID 与权限范围）
        permission_subquery = RoleMenuButtonModel.objects.filter(
            role_id=OuterRef("id"), menu_button_id=menu_button_id
        ).values("id", "permission_range")[:1]

        # 2. 查询所有角色，左连接标注权限信息（数据库层面分页）
        role_queryset = (
            RoleModel.objects.annotate(
                role_menu_button_id=Subquery(permission_subquery.values("id")),
                permission_range_annotated=Subquery(
                    permission_subquery.values("permission_range")
                ),
            )
            .order_by("sort")
            .values("id", "name", "role_menu_button_id", "permission_range_annotated")
        )
        page = self.paginate_queryset(role_queryset)

        # 3. 提取已分配权限的记录 ID，批量获取其关联部门
        role_menu_button_ids = [
            item["role_menu_button_id"]
            for item in page
            if item["role_menu_button_id"] is not None
        ]
        dept_map = self._get_dept_map(role_menu_button_ids)

        # 4. 组装结果：未分配权限的角色返回默认值（has_permission=False）
        result = []
        for item in page:
            record_id = item["role_menu_button_id"]
            result.append(
                {
                    "role": item["id"],
                    "role_name": item["name"],
                    "menu_button": menu_button_id if record_id else None,
                    "need_data_scope": need_data_scope if need_data_scope is not None else True,
                    "role_menu_button": record_id,
                    "has_permission": record_id is not None,
                    "permission_range": (
                        item["permission_range_annotated"] if record_id else 0
                    ),
                    "dept": dept_map.get(record_id, []),
                }
            )
        return self.get_paginated_response(result)

    @extend_schema(summary="通过角色授权按钮", extensions={"x-function": "RolesButton"})
    @action(methods=["GET"], detail=False)
    def roles_button(self, request, *args, **kwargs):
        """
        角色维度：查询指定菜单下所有按钮对该角色的授权情况
        :param role_id: 角色 ID（query 参数，必传）
        :param menu_id: 菜单 ID（query 参数，必传）
        :return: 分页结果，每项包含 menu / menu_button / menu_button_name / button_type /
                 need_data_scope / role / role_menu_button / has_permission / permission_range / dept
        :description: 前端配合：通过角色授权按钮页面，用于展示"该角色在某菜单下拥有哪些按钮权限"。
        实现思路：先查出指定菜单下的所有按钮，再用子查询左连接标注该角色在每个按钮上的
        权限记录，最后批量补充关联部门 ID 列表
        """
        role_id = request.query_params.get("role_id")
        menu_id = request.query_params.get("menu_id")

        # 1. 查询指定菜单下的所有按钮
        menu_buttons = MenuButtonModel.objects.filter(menu_id=menu_id).values(
            "id", "name", "button_type", "need_data_scope"
        )

        # 2. 子查询：查找该角色在每个按钮上的权限记录（记录 ID 与权限范围）
        permission_subquery = RoleMenuButtonModel.objects.filter(
            role_id=role_id, menu_button_id=OuterRef("id")
        ).values("id", "permission_range")[:1]

        # 3. 左连接标注权限信息（数据库层面分页）
        button_queryset = menu_buttons.annotate(
            role_menu_button_id=Subquery(permission_subquery.values("id")),
            permission_range_annotated=Subquery(
                permission_subquery.values("permission_range")
            ),
        ).order_by("sort")
        page = self.paginate_queryset(button_queryset)

        # 4. 提取已分配权限的记录 ID，批量获取其关联部门
        role_menu_button_ids = [
            item["role_menu_button_id"]
            for item in page
            if item["role_menu_button_id"] is not None
        ]
        dept_map = self._get_dept_map(role_menu_button_ids)

        # 5. 组装结果：未分配权限的按钮返回默认值（has_permission=False）
        result = []
        for item in page:
            record_id = item["role_menu_button_id"]
            result.append(
                {
                    "menu": menu_id,
                    "menu_button": item["id"],
                    "menu_button_name": item.get("name"),
                    "button_type": item.get("button_type"),
                    "need_data_scope": item.get("need_data_scope", True),
                    "role": role_id,
                    "role_menu_button": record_id,
                    "has_permission": record_id is not None,
                    "permission_range": (
                        item["permission_range_annotated"] if record_id else 0
                    ),
                    "dept": dept_map.get(record_id, []),
                }
            )
        return self.get_paginated_response(result)

    @extend_schema(summary="批量更新按钮权限范围", extensions={"x-function": "BatchUpdate"})
    @action(methods=["POST"], detail=False)
    def batch_update(self, request, *args, **kwargs):
        """
        统一设置模式：批量更新角色在指定菜单下所有已分配按钮的权限范围
        :param role_id: 角色 ID（body 参数，必传）
        :param menu_id: 菜单 ID（body 参数，必传）
        :param permission_range: 数据权限范围 0-4（默认 0）
        :param dept: 关联部门 ID 列表，仅 permission_range=3（自定义部门）时生效
        :return: { updated_count: 实际更新的记录数 }
        :description: 前端配合：授权按钮面板"统一设置"模式调用，入参格式
        { "role_id": 5, "menu_id": 3, "permission_range": 3, "dept": [1, 2] }。
        仅作用于该角色在该菜单下已分配权限（存在记录）的按钮；
        事务内批量更新权限范围与关联部门，保证数据一致性
        """
        role_id = request.data.get("role_id")
        menu_id = request.data.get("menu_id")
        permission_range = request.data.get("permission_range", 0)
        dept_ids = request.data.get("dept", [])

        # 参数校验：role_id / menu_id 必传，permission_range 必须在合法范围内
        if not role_id or not menu_id:
            return error_response(message="参数错误：role_id 与 menu_id 必传")
        if permission_range not in dict(RoleMenuButtonModel.DATASCOPE_CHOICES):
            return error_response(message="参数错误：permission_range 不在合法范围内")

        # 查询该角色在该菜单下已分配权限的按钮记录（先固化为列表，避免更新后重复查询）
        # 仅处理需要数据访问的按钮（无需数据访问的按钮默认全部数据，不参与范围设置）
        records = list(
            RoleMenuButtonModel.objects.filter(
                role_id=role_id,
                menu_button__menu_id=menu_id,
                menu_button__need_data_scope=True,
            )
        )

        with transaction.atomic():
            # 批量更新权限范围（单条 UPDATE SQL）
            updated_count = RoleMenuButtonModel.objects.filter(
                id__in=[record.id for record in records]
            ).update(permission_range=permission_range)
            # 自定义部门：写入关联部门；其他范围：清空关联部门
            for record in records:
                if permission_range == PERMISSION_RANGE_CUSTOM_DEPT:
                    record.dept.set(dept_ids)  # type: ignore[attr-defined] 告诉类型检查器忽略此处的方法属性检查
                else:
                    record.dept.clear()  # type: ignore[attr-defined] 告诉类型检查器忽略此处的方法属性检查

        return success_response(message=f"批量更新成功{updated_count}条权限", data={"updated_count": updated_count})

    @extend_schema(summary="批量开启/关闭按钮权限", extensions={"x-function": "BatchPermission"})
    @action(methods=["POST"], detail=False)
    def batch_permission(self, request, *args, **kwargs):
        """
        表头批量授权：一次性开启或关闭角色在指定菜单下所有按钮的权限
        :param role_id: 角色 ID（body 参数，必传）
        :param menu_id: 菜单 ID（body 参数，必传）
        :param has_permission: 是否开启权限（true=批量创建未分配记录，false=批量删除全部记录）
        :param permission_range: 数据权限范围 0-4（仅开启时生效，默认 0）
        :param dept: 关联部门 ID 列表，仅开启且 permission_range=3（自定义部门）时生效
        :return: 开启时 { created: [{ menu_button, role_menu_button, permission_range, dept }] }；
                 关闭时 { deleted_count: 删除的记录数 }
        :description: 前端配合：授权按钮面板"权限分配"列表头开关调用，单次请求完成全量授权或取消。
        开启时仅为未分配权限的按钮创建记录（已分配的不受影响），无需数据访问的按钮强制
        权限范围 4（全部）且不关联部门，与创建序列化器兜底规则一致；关闭时删除该角色在该
        菜单下全部按钮权限记录（级联清理关联部门）
        """
        role_id = request.data.get("role_id")
        menu_id = request.data.get("menu_id")
        has_permission = request.data.get("has_permission")
        permission_range = request.data.get("permission_range", 0)
        dept_ids = request.data.get("dept", [])

        # 参数校验：role_id / menu_id 必传，has_permission 必须为布尔值，permission_range 必须在合法范围内
        if not role_id or not menu_id:
            return error_response(message="参数错误：role_id 与 menu_id 必传")
        if not isinstance(has_permission, bool):
            return error_response(message="参数错误：has_permission 必须为布尔值")
        if permission_range not in dict(RoleMenuButtonModel.DATASCOPE_CHOICES):
            return error_response(message="参数错误：permission_range 不在合法范围内")

        # 批量关闭：删除该角色在该菜单下全部按钮权限记录（先固化为列表，级联清理关联部门）
        if not has_permission:
            records = list(
                RoleMenuButtonModel.objects.filter(
                    role_id=role_id, menu_button__menu_id=menu_id
                )
            )
            with transaction.atomic():
                RoleMenuButtonModel.objects.filter(
                    id__in=[record.id for record in records]
                ).delete()
            return success_response(
                message=f"批量关闭成功，共移除{len(records)}条权限",
                data={"deleted_count": len(records)},
            )

        # 批量开启：查询该菜单下所有按钮与已分配的按钮 ID，仅创建未分配记录的按钮（已分配的不受影响）
        menu_buttons = MenuButtonModel.objects.filter(menu_id=menu_id).values(
            "id", "need_data_scope"
        )
        existing_button_ids = set(
            RoleMenuButtonModel.objects.filter(
                role_id=role_id, menu_button__menu_id=menu_id
            ).values_list("menu_button_id", flat=True)
        )

        # 记录无需数据访问的按钮：强制权限范围 4（全部），与创建序列化器兜底规则一致
        need_data_scope_map = {
            button["id"]: button["need_data_scope"]
            for button in menu_buttons
            if button["id"] not in existing_button_ids
        }

        with transaction.atomic():
            # 逐条创建：bulk_create 在部分数据库（如 SQLite）下不回填主键，
            # 导致关联部门设置与返回记录 ID 不可用，故改为循环创建
            created_records = []
            for button_id, need_scope in need_data_scope_map.items():
                record = RoleMenuButtonModel.objects.create(
                    role_id=role_id,
                    menu_button_id=button_id,
                    permission_range=4 if not need_scope else permission_range,
                )
                created_records.append(record)
                # 自定义部门且需要数据访问的按钮：写入关联部门（无需数据访问的按钮不关联部门）
                if permission_range == PERMISSION_RANGE_CUSTOM_DEPT and need_scope:
                    record.dept.set(dept_ids)  # type: ignore[attr-defined] 告诉类型检查器忽略此处的方法属性检查

        created_data = [
            {
                "menu_button": record.menu_button_id,
                "role_menu_button": record.id,
                "permission_range": record.permission_range,
                "dept": (
                    dept_ids
                    if need_data_scope_map.get(record.menu_button_id)
                    and permission_range == PERMISSION_RANGE_CUSTOM_DEPT
                    else []
                ),
            }
            for record in created_records
        ]
        return success_response(
            message=f"批量开启成功，共新增{len(created_data)}条权限",
            data={"created": created_data},
        )

    @extend_schema(summary="批量更新角色权限范围", extensions={"x-function": "BatchButtonUpdate"})
    @action(methods=["POST"], detail=False)
    def batch_button_update(self, request, *args, **kwargs):
        """
        统一设置模式：批量更新指定按钮下所有已分配角色的权限范围
        :param menu_button_id: 菜单按钮 ID（body 参数，必传）
        :param permission_range: 数据权限范围 0-4（默认 0）
        :param dept: 关联部门 ID 列表，仅 permission_range=3（自定义部门）时生效
        :return: { updated_count: 实际更新的记录数 }
        :description: 前端配合：通过按钮授权角色面板"统一设置"模式调用，入参格式
        { "menu_button_id": 3, "permission_range": 3, "dept": [1, 2] }。
        仅作用于该按钮下已分配权限（存在记录）的角色；
        事务内批量更新权限范围与关联部门，保证数据一致性
        """
        menu_button_id = request.data.get("menu_button_id")
        permission_range = request.data.get("permission_range", 0)
        dept_ids = request.data.get("dept", [])

        # 参数校验：menu_button_id 必传，permission_range 必须在合法范围内
        if not menu_button_id:
            return error_response(message="参数错误：menu_button_id 必传")
        if permission_range not in dict(RoleMenuButtonModel.DATASCOPE_CHOICES):
            return error_response(message="参数错误：permission_range 不在合法范围内")

        # 查询该按钮下已分配权限的角色记录（先固化为列表，避免更新后重复查询）
        # 仅处理需要数据访问的按钮（无需数据访问的按钮默认全部数据，不参与范围设置）
        records = list(
            RoleMenuButtonModel.objects.filter(
                menu_button_id=menu_button_id,
                menu_button__need_data_scope=True,
            )
        )

        with transaction.atomic():
            # 批量更新权限范围（单条 UPDATE SQL）
            updated_count = RoleMenuButtonModel.objects.filter(
                id__in=[record.id for record in records]
            ).update(permission_range=permission_range)
            # 自定义部门：写入关联部门；其他范围：清空关联部门
            for record in records:
                if permission_range == PERMISSION_RANGE_CUSTOM_DEPT:
                    record.dept.set(dept_ids)  # type: ignore[attr-defined] 告诉类型检查器忽略此处的方法属性检查
                else:
                    record.dept.clear()  # type: ignore[attr-defined] 告诉类型检查器忽略此处的方法属性检查

        return success_response(message=f"批量更新成功{updated_count}条权限", data={"updated_count": updated_count})

    @extend_schema(summary="批量开启/关闭角色权限", extensions={"x-function": "BatchButtonPermission"})
    @action(methods=["POST"], detail=False)
    def batch_button_permission(self, request, *args, **kwargs):
        """
        表头批量授权：一次性开启或关闭指定按钮下所有角色的权限
        :param menu_button_id: 菜单按钮 ID（body 参数，必传）
        :param has_permission: 是否开启权限（true=批量创建未分配记录，false=批量删除全部记录）
        :param permission_range: 数据权限范围 0-4（仅开启时生效，默认 0）
        :param dept: 关联部门 ID 列表，仅开启且 permission_range=3（自定义部门）时生效
        :return: 开启时 { created: [{ role, role_menu_button, permission_range, dept }] }；
                 关闭时 { deleted_count: 删除的记录数 }
        :description: 前端配合：通过按钮授权角色面板"权限分配"列表头开关调用，单次请求完成全量授权或取消。
        开启时仅为未分配权限的角色创建记录（已分配的不受影响），无需数据访问的按钮强制
        权限范围 4（全部）且不关联部门；关闭时删除该按钮下全部角色权限记录（级联清理关联部门）
        """
        menu_button_id = request.data.get("menu_button_id")
        has_permission = request.data.get("has_permission")
        permission_range = request.data.get("permission_range", 0)
        dept_ids = request.data.get("dept", [])

        # 参数校验：menu_button_id 必传，has_permission 必须为布尔值，permission_range 必须在合法范围内
        if not menu_button_id:
            return error_response(message="参数错误：menu_button_id 必传")
        if not isinstance(has_permission, bool):
            return error_response(message="参数错误：has_permission 必须为布尔值")
        if permission_range not in dict(RoleMenuButtonModel.DATASCOPE_CHOICES):
            return error_response(message="参数错误：permission_range 不在合法范围内")

        # 批量关闭：删除该按钮下全部角色权限记录（先固化为列表，级联清理关联部门）
        if not has_permission:
            records = list(
                RoleMenuButtonModel.objects.filter(menu_button_id=menu_button_id)
            )
            with transaction.atomic():
                RoleMenuButtonModel.objects.filter(
                    id__in=[record.id for record in records]
                ).delete()
            return success_response(
                message=f"批量关闭成功，共移除{len(records)}条权限",
                data={"deleted_count": len(records)},
            )

        # 查询按钮属性：是否需要数据访问（无需数据访问的按钮强制权限范围 4，与创建序列化器兜底规则一致）
        need_data_scope = (
            MenuButtonModel.objects.filter(pk=menu_button_id)
            .values_list("need_data_scope", flat=True)
            .first()
        )
        if need_data_scope is None:
            return error_response(message="参数错误：按钮不存在")

        # 批量开启：查询所有角色与已分配的角色 ID，仅创建未分配记录的角色（已分配的不受影响）
        existing_role_ids = set(
            RoleMenuButtonModel.objects.filter(
                menu_button_id=menu_button_id
            ).values_list("role_id", flat=True)
        )

        with transaction.atomic():
            # 逐条创建：bulk_create 在部分数据库（如 SQLite）下不回填主键，
            # 导致关联部门设置与返回记录 ID 不可用，故改为循环创建
            created_records = []
            for role_id in RoleModel.objects.values_list("id", flat=True):
                if role_id in existing_role_ids:
                    continue
                record = RoleMenuButtonModel.objects.create(
                    role_id=role_id,
                    menu_button_id=menu_button_id,
                    permission_range=4 if not need_data_scope else permission_range,
                )
                created_records.append(record)
                # 自定义部门且按钮需要数据访问：写入关联部门（无需数据访问的按钮不关联部门）
                if permission_range == PERMISSION_RANGE_CUSTOM_DEPT and need_data_scope:
                    record.dept.set(dept_ids)  # type: ignore[attr-defined] 告诉类型检查器忽略此处的方法属性检查

        created_data = [
            {
                "role": record.role_id,
                "role_menu_button": record.id,
                "permission_range": record.permission_range,
                "dept": (
                    dept_ids
                    if permission_range == PERMISSION_RANGE_CUSTOM_DEPT
                    else []
                ),
            }
            for record in created_records
        ]
        return success_response(
            message=f"批量开启成功，共新增{len(created_data)}条权限",
            data={"created": created_data},
        )

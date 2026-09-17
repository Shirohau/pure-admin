import itertools

from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import success_response, error_response
from extends.drf.views_mixins import *
from .filters import RoleMenuFieldFilter
from .models import (
    FUNC_PERMISSION_DEFINITIONS,
    PERMISSION_LEVEL_DENIED,
    PERMISSION_LEVEL_READ,
    PERMISSION_LEVEL_WRITE,
    RoleMenuFieldModel,
)
from .serializers import RoleMenuFieldSerializer
from ..menu_field.models import MenuFieldModel
from ..role.models import RoleModel


def _validate_permission_level(permission_level):
    """校验数据权限等级，返回 int 或 None（未传）"""
    if permission_level is None:
        return None
    try:
        permission_level = int(permission_level)
    except (TypeError, ValueError):
        return None
    if permission_level not in (PERMISSION_LEVEL_DENIED, PERMISSION_LEVEL_READ, PERMISSION_LEVEL_WRITE):
        return None
    return permission_level


def _validate_func_permissions(func_permissions):
    """校验功能权限集，返回 dict 或 None（未传）

    白名单机制：仅保留 FUNC_PERMISSION_DEFINITIONS 中声明的功能权限 key（可配置扩展，
    新增权限只需在定义处追加），未知 key 一律丢弃，保证落库数据干净统一。
    """
    if func_permissions is None:
        return None
    if not isinstance(func_permissions, dict):
        return None
    return {
        key: bool(value)
        for key, value in func_permissions.items()
        if key in FUNC_PERMISSION_DEFINITIONS
    }


def _upsert_role_menu_field(role_ids, field_ids, permission_level=None, func_permissions=None):
    """批量 upsert 角色↔字段权限记录。

    创建时机：分配权限的那一刻落库（记录不存在则创建）；
    更新时机：记录存在则按传入字段部分更新（permission_level / func_permissions 哪个传了就更新哪个）。
    独立语义：仅传 func_permissions 时，新记录的 permission_level 为 NULL（不默认任何数据等级，
    避免“勾选可下载联动点亮可读写”）；仅传 permission_level 时不改动 func_permissions。

    功能权限合并规则：功能权限之间互不排斥（可下载/可打印可同时选中）。
    仅传 func_permissions（未传 permission_level）时采用合并式更新，只覆盖传入的 key，
    避免批量全选“可下载”时误清掉已勾选的“可打印”；
    同时传入 permission_level（如批量勾选“禁止”时联动关闭全部功能权限）时仍整体覆盖。
    """
    existing_map = {
        (obj.role_id, obj.menu_field_id): obj
        for obj in RoleMenuFieldModel.objects.filter(
            role_id__in=role_ids,
            menu_field_id__in=field_ids,
        )
    }
    to_update, to_create = [], []
    for role_id, field_id in itertools.product(role_ids, field_ids):
        obj = existing_map.get((role_id, field_id))
        if obj:
            if permission_level is not None:
                obj.permission_level = permission_level
            if func_permissions is not None:
                if permission_level is None:
                    # 纯功能权限更新：合并式更新（功能权限互不排斥，只覆盖传入的 key）
                    obj.func_permissions = {
                        **(obj.func_permissions or {}),
                        **func_permissions,
                    }
                else:
                    # 带数据等级更新（如批量“禁止”联动关闭全部功能权限）：整体覆盖
                    obj.func_permissions = func_permissions
            obj.update_dt = timezone.now()
            to_update.append(obj)
        else:
            to_create.append(RoleMenuFieldModel(
                role_id=role_id,
                menu_field_id=field_id,
                permission_level=permission_level,
                func_permissions=dict(func_permissions) if func_permissions is not None else {},
            ))
    if to_create:
        RoleMenuFieldModel.objects.bulk_create(to_create)
    if to_update:
        update_fields = ["update_dt"]
        if permission_level is not None:
            update_fields.append("permission_level")
        if func_permissions is not None:
            update_fields.append("func_permissions")
        RoleMenuFieldModel.objects.bulk_update(to_update, update_fields)


@extend_schema(tags=["角色菜单字段"])
class RoleMenuFieldViewSet(CrudViewSet):
    """角色菜单字段视图：提供角色↔字段授权面板的查询与单条/批量权限操作接口。"""
    queryset = RoleMenuFieldModel.objects.all().select_related(
        'role', 'menu_field', 'menu_field__menu')
    serializer_class = RoleMenuFieldSerializer
    filterset_class = RoleMenuFieldFilter
    extra_filter_class = []

    @extend_schema(summary="获取功能权限定义", extensions={'x-function': 'FuncPermissionDefinitions'})
    @action(methods=["GET"], detail=False)
    def func_permission_definitions(self, request, *args, **kwargs):
        """返回功能权限目录（key -> label），前端据此动态渲染功能权限列。"""
        data = [
            {"key": key, "label": label}
            for key, label in FUNC_PERMISSION_DEFINITIONS.items()
        ]
        return success_response(message="功能权限定义获取成功", data=data)

    @extend_schema(summary="通过字段授权角色", extensions={'x-function': 'FieldRoles'})
    @action(methods=["GET"], detail=False)
    def field_roles(self, request, *args, **kwargs):
        """
        根据字段，查询所有角色分配的权限（用于“菜单字段→分配角色”面板）。
        1、先在 RoleModel 中查询出所有的角色
        2、再根据菜单字段，在 RoleMenuFieldModel 中查询出权限
        3、用 1 查询结果做左连接
        """
        menu_field_id = request.query_params.get('menu_field_id')
        if not menu_field_id:
            return error_response(message="参数错误：menu_field_id 为必传参数")
        # 第一步：获取所有角色，并标注是否拥有该字段权限（子查询左连接）
        role_menu_field_subquery = RoleMenuFieldModel.objects.filter(
            role_id=OuterRef('id'),
            menu_field_id=menu_field_id
        ).values('id', 'permission_level', 'func_permissions')[:1]

        queryset = RoleModel.objects.annotate(
            role_menu_field_id=Subquery(role_menu_field_subquery.values('id')),
            permission_level_annotated=Subquery(role_menu_field_subquery.values('permission_level')),
            func_permissions_annotated=Subquery(role_menu_field_subquery.values('func_permissions')),
        ).order_by('sort').values(
            'id',
            'name',
            'role_menu_field_id',
            'permission_level_annotated',
            'func_permissions_annotated',
        )
        # 使用 DRF 分页器对 QuerySet 分页（数据库级别）
        page = self.paginate_queryset(queryset)

        # 组装结果：无权限记录的角色按“默认全部权限”语义返回（has_permission=False）
        result = []
        for item in page:
            perm_id = item['role_menu_field_id']
            result.append({
                "role": item["id"],
                "role_name": item["name"],
                "menu_field": menu_field_id if perm_id else None,
                "role_menu_field": perm_id,
                "has_permission": perm_id is not None,
                "permission_level": item["permission_level_annotated"] if perm_id else None,
                "func_permissions": (item["func_permissions_annotated"] or {}) if perm_id else {},
            })
        return self.get_paginated_response(result)

    @extend_schema(summary="通过角色授权字段", extensions={'x-function': 'RoleFields'})
    @action(methods=["GET"], detail=False)
    def role_fields(self, request, *args, **kwargs):
        """
        根据角色，授权字段（用于“角色→菜单字段”授权面板）。
        1、先在 MenuFieldModel 中查询出指定菜单下的所有字段
        2、再根据角色，在 RoleMenuFieldModel 中查询出权限
        3、用 1 查询结果做左连接
        """
        role_id = request.query_params.get('role_id')
        menu_id = request.query_params.get('menu_id')
        if not role_id or not menu_id:
            return error_response(message="参数错误：role_id 与 menu_id 为必传参数")
        # 第一步：获取指定菜单下的所有字段
        menu_field = MenuFieldModel.objects.filter(menu_id=menu_id).values('id', 'verbose_name')

        # 第二步：为每个字段标注该角色是否拥有权限（子查询左连接）
        permission_subquery = RoleMenuFieldModel.objects.filter(
            role_id=role_id,
            menu_field_id=OuterRef('id')
        ).values('id', 'permission_level', 'func_permissions')[:1]

        queryset = menu_field.annotate(
            role_menu_field_id=Subquery(permission_subquery.values('id')),
            permission_level_annotated=Subquery(permission_subquery.values('permission_level')),
            func_permissions_annotated=Subquery(permission_subquery.values('func_permissions'))
        ).order_by('sort')

        # 使用 DRF 分页器对 QuerySet 分页（数据库级别）
        page = self.paginate_queryset(queryset)

        # 组装结果：无权限记录的字段按“默认全部权限”语义返回（has_permission=False）
        result = []
        for item in page:
            perm_id = item['role_menu_field_id']
            result.append({
                "menu": menu_id,
                "menu_field": item["id"],
                "menu_field_name": item.get("verbose_name"),
                "role": role_id,
                "role_menu_field": perm_id,
                "has_permission": perm_id is not None,
                "permission_level": item["permission_level_annotated"] if perm_id else None,
                "func_permissions": (item["func_permissions_annotated"] or {}) if perm_id else {},
            })
        return self.get_paginated_response(result)

    @extend_schema(summary="单条保存权限", extensions={'x-function': 'SavePermission'})
    @action(methods=["POST"], detail=False)
    def save_permission(self, request, *args, **kwargs):
        """
        单条保存角色↔字段权限（无记录则创建，有记录则更新，upsert 语义）。

        POST body:
            - role:          int, 必传, 角色ID
            - menu_field:    int, 必传, 菜单字段ID
            - permission_level: int, 可选, 数据权限等级 (0=禁止/1=只读/2=可读写)
            - func_permissions: dict, 可选, 功能权限集，如 {"can_download": true}

        特殊规则：
            - permission_level 与 func_permissions 均不传 → 删除记录（取消全部权限，回到默认全部权限语义）
            - permission_level 显式传 null → 清除数据权限等级（保留功能权限，两者完全独立）
            - 记录不存在时创建，permission_level 不默认任何等级（null）、func_permissions 默认 {}
        """
        data = request.data
        role_id = data.get('role')
        menu_field_id = data.get('menu_field')
        permission_level = _validate_permission_level(data.get('permission_level'))
        func_permissions = _validate_func_permissions(data.get('func_permissions'))
        has_level = 'permission_level' in data
        has_funcs = 'func_permissions' in data

        if not role_id or not menu_field_id:
            return error_response(message="参数错误：role 与 menu_field 为必传参数")
        if has_level and permission_level is None and data.get('permission_level') is not None:
            return error_response(message="参数错误：permission_level 仅支持 0/1/2 或 null")
        if has_funcs and func_permissions is None:
            return error_response(message="参数错误：func_permissions 必须是对象")

        with transaction.atomic():
            obj = RoleMenuFieldModel.objects.filter(
                role_id=role_id, menu_field_id=menu_field_id
            ).first()
            if not has_level and not has_funcs:
                # 取消全部权限 → 删除记录，回到“默认拥有全部权限”语义
                if obj:
                    obj.delete()
                return success_response(message="已恢复默认权限")
            if obj:
                if has_level:
                    obj.permission_level = permission_level
                if has_funcs:
                    obj.func_permissions = func_permissions or {}
                obj.save()
            else:
                obj = RoleMenuFieldModel.objects.create(
                    role_id=role_id,
                    menu_field_id=menu_field_id,
                    permission_level=permission_level,
                    func_permissions=dict(func_permissions) if func_permissions is not None else {},
                )
        serializer = RoleMenuFieldSerializer(obj, context=self.get_serializer_context())
        return success_response(message="保存成功", data=serializer.data)

    @extend_schema(summary="从角色页面批量授权菜单字段", extensions={'x-function': 'BatchUpdateRoleFields'})
    @action(methods=["POST"], detail=False)
    def batch_update_role_fields(self, request, *args, **kwargs):
        """
        从角色页面批量授权菜单字段：对指定角色在指定菜单下的当前页字段设置权限。

        POST body:
            - role:          int, 必传, 角色ID
            - menu:          int, 必传, 菜单ID（校验 field_ids 属于该菜单）
            - field_ids:     list[int], 必传, 当前页的菜单字段ID列表
            - permission_level: int, 可选, 数据权限等级 (0=禁止/1=只读/2=可读写)
            - func_permissions: dict, 可选, 功能权限集，如 {"can_download": true}

        规则：permission_level 与 func_permissions 至少传一个；
        记录不存在则自动创建，存在则更新对应字段。
        """
        data = request.data
        role_id = data.get('role')
        menu_id = data.get('menu')
        field_ids = data.get('field_ids')
        permission_level = _validate_permission_level(data.get('permission_level'))
        func_permissions = _validate_func_permissions(data.get('func_permissions'))

        if not role_id or not menu_id or not field_ids:
            return error_response(message="参数错误：role、menu、field_ids 为必传参数")
        if permission_level is None and func_permissions is None:
            return error_response(message="参数错误：permission_level 与 func_permissions 至少传一个")

        # 校验 field_ids 全部属于指定菜单，防止越权写入其他菜单的字段
        valid_field_ids = set(
            MenuFieldModel.objects.filter(menu_id=int(menu_id), id__in=field_ids).values_list('id', flat=True)
        )
        if not valid_field_ids:
            return error_response(message="未找到匹配的菜单字段")

        with transaction.atomic():
            _upsert_role_menu_field(
                [int(role_id)],
                list(valid_field_ids),
                permission_level,
                func_permissions,
            )
        return success_response(message="批量授权成功")

    @extend_schema(summary="从菜单字段页面批量授权角色", extensions={'x-function': 'BatchUpdateFieldRoles'})
    @action(methods=["POST"], detail=False)
    def batch_update_field_roles(self, request, *args, **kwargs):
        """
        从菜单字段页面批量授权角色：为指定菜单字段设置当前页角色的权限。

        POST body:
            - menu_field:   int, 必传, 菜单字段ID
            - role_ids:     list[int], 必传, 当前页的角色ID列表
            - permission_level: int, 可选, 数据权限等级 (0=禁止/1=只读/2=可读写)
            - func_permissions: dict, 可选, 功能权限集，如 {"can_download": true}

        规则：permission_level 与 func_permissions 至少传一个；
        记录不存在则自动创建，存在则更新对应字段。
        """
        data = request.data
        menu_field_id = data.get('menu_field')
        role_ids = data.get('role_ids')
        permission_level = _validate_permission_level(data.get('permission_level'))
        func_permissions = _validate_func_permissions(data.get('func_permissions'))

        if not menu_field_id or not role_ids:
            return error_response(message="参数错误：menu_field 与 role_ids 为必传参数")
        if permission_level is None and func_permissions is None:
            return error_response(message="参数错误：permission_level 与 func_permissions 至少传一个")

        # 校验角色存在
        valid_role_ids = set(RoleModel.objects.filter(id__in=role_ids).values_list('id', flat=True))
        if not valid_role_ids:
            return error_response(message="未找到匹配的角色")

        with transaction.atomic():
            _upsert_role_menu_field(
                list(valid_role_ids),
                [int(menu_field_id)],
                permission_level,
                func_permissions,
            )
        return success_response(message="批量授权成功")

    @extend_schema(summary="批量移除权限", extensions={'x-function': 'BatchDestroy'})
    @action(methods=["DELETE"], detail=False)
    def batch_destroy(self, request, *args, **kwargs):
        """
        批量移除权限（表头取消全选时调用），支持两种模式：

        模式1（角色页面）：{ "role": 5, "menu": 3, "field_ids": [1, 2] }
            → 移除角色5在指定字段上的权限（field_ids 必传，仅作用于当前页字段）

        模式2（菜单字段页面）：{ "menu_field": 101, "role_ids": [1, 2] }
            → 移除指定字段在指定角色上的权限（role_ids 必传，仅作用于当前页角色）

        特殊规则：func_permissions 非空（显式配置过，含全 false 的显式关闭状态）的记录
        不会被删除，仅清除数据权限等级（permission_level 置 NULL，不再默认可读写），
        保留功能权限，保证"功能权限"与"数据权限等级"完全独立、互不联动。
        """
        data = request.data
        menu_field_id = data.get('menu_field')
        role_ids = data.get('role_ids')
        role_id = data.get('role')
        menu_id = data.get('menu')
        field_ids = data.get('field_ids')

        with transaction.atomic():
            qs = RoleMenuFieldModel.objects.all()
            if menu_field_id is not None:
                # 模式2：指定字段 + 指定角色（当前页）
                if not role_ids:
                    return error_response(message="参数错误：role_ids 为必传参数")
                qs = qs.filter(menu_field_id=int(menu_field_id), role_id__in=role_ids)
            elif role_id is not None and menu_id is not None:
                # 模式1：指定角色 + 指定字段（当前页）
                if not field_ids:
                    return error_response(message="参数错误：field_ids 为必传参数")
                qs = qs.filter(role_id=int(role_id), menu_field_id__in=field_ids)
            else:
                return error_response(message="参数错误：需传 menu_field+role_ids 或 role+menu+field_ids")

            records = list(qs)
            # 显式配置过功能权限的记录（fp 非空，含全 false 的显式关闭状态如
            # {can_download:false}）：仅清除数据权限等级（置 NULL），功能权限不受影响；
            # 若删除记录会丢失关闭状态（后端恢复"默认全部权限"），故必须保留
            keep_ids = [
                obj.id for obj in records
                if (obj.func_permissions or {})
            ]
            if keep_ids:
                RoleMenuFieldModel.objects.filter(id__in=keep_ids).update(permission_level=None)
            # 从未配置过功能权限（fp 为空）的记录直接删除（回到“默认拥有全部权限”语义）
            deleted_count, _ = RoleMenuFieldModel.objects.filter(
                id__in=[obj.id for obj in records if obj.id not in keep_ids]
            ).delete()
        return success_response(message=f"批量删除成功，共移除 {deleted_count} 条记录")

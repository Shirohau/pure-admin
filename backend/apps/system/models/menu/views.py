from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import success_response, error_response
from extends.drf.views_mixins import *

from .filters import MenuFilter
from .models import MenuModel
from .resources import MenuExportResource, MenuImportResource
from .serializers import MenuSerializer, MenuCreateSerializer, MenuUpdateSerializer, MenuRoutesSerializer
from ..menu_button.models import MenuButtonModel
from ..menu_field.models import MenuFieldModel
from ..role_menu_button.models import RoleMenuButtonModel
from ..role_menu_field.models import FUNC_PERMISSION_DEFINITIONS, RoleMenuFieldModel


@extend_schema(tags=["菜单"])
class MenuViewSet(CrudViewSet, MoveMixin):
    queryset = MenuModel.objects.filter().prefetch_related('role')
    serializer_class = MenuSerializer
    create_serializer_class = MenuCreateSerializer
    update_serializer_class = MenuUpdateSerializer
    filterset_class = MenuFilter
    export_resource_class = MenuExportResource
    import_resource_class = MenuImportResource

    @extend_schema(summary="获取权限路由", extensions={'x-function': 'Routes'})
    @action(methods=['GET'], detail=False)
    def routes(self, request, *args, **kwargs):
        """
        获取菜单路由列表：
            - 超级管理员（is_superuser）或具有 'admin' 角色的用户返回全部菜单；
            - 普通用户仅返回其角色关联的菜单。
        """
        user = request.user
        # 判断是否为管理员：超级管理员或具有 admin 角色的用户返回全部菜单
        if user.is_superuser or user.role.filter(name='admin').exists():
            queryset = self.queryset.all().order_by('sort')
        else:
            # 普通用户仅返回其角色关联的菜单
            queryset = self.queryset.filter(role__in=user.role.all()).distinct().order_by('sort')
        serializer = MenuRoutesSerializer(queryset, many=True)
        return success_response(message="列表查询成功", data=serializer.data)

    @extend_schema(summary="获取页面按钮+字段权限", extensions={'x-function': 'PagePerms'})
    @action(methods=['GET'], detail=False, url_path='page-perms')
    def page_perms(self, request, *args, **kwargs):
        """
        根据菜单 name 获取当前用户在该页面下的按钮权限 key 列表 + 字段权限
        前端按页面增量加载，一次请求同时获取按钮和字段权限
        """
        menu_name = request.query_params.get('name')
        if not menu_name:
            return error_response(message="缺少菜单 name 参数")

        user = request.user
        menu = MenuModel.objects.filter(name=menu_name).first()
        if not menu:
            return error_response(message=f"菜单 '{menu_name}' 不存在")

        # --- 按钮权限 ---
        menu_buttons = MenuButtonModel.objects.filter(menu=menu)
        if user.is_superuser or user.role.filter(name='admin').exists():
            buttons = list(menu_buttons.values_list('key', flat=True))
        else:
            buttons = list(
                RoleMenuButtonModel.objects.filter(
                    role__in=user.role.all(),
                    menu_button__in=menu_buttons
                ).values_list('menu_button__key', flat=True).distinct()
            )

        # --- 字段权限 ---
        menu_fields = MenuFieldModel.objects.filter(menu=menu)
        if user.is_superuser or user.role.filter(name='admin').exists():
            fields = [
                {
                    'field_name': mf.field_name,
                    'permission_level': 2,
                    # 管理员默认拥有全部功能权限（按 FUNC_PERMISSION_DEFINITIONS 动态生成）
                    'func_permissions': {key: True for key in FUNC_PERMISSION_DEFINITIONS},
                }
                for mf in menu_fields
            ]
        else:
            role_menu_fields = RoleMenuFieldModel.objects.filter(
                role__in=user.role.all(),
                menu_field__in=menu_fields
            ).select_related('menu_field')
            # 合并规则：访问权限取最大值（禁止(0)一票否决）；功能权限取 OR（任一角色允许即允许）。
            # 功能权限按 FUNC_PERMISSION_DEFINITIONS 动态遍历，新增功能权限无需改动此处；
            # 未知 key（历史遗留）一律丢弃，保证返回数据只含已定义的功能权限。
            field_map = {}
            for rmf in role_menu_fields:
                fn = rmf.menu_field.field_name
                pl = rmf.permission_level
                funcs = {
                    key: bool(value)
                    for key, value in (rmf.func_permissions or {}).items()
                    if key in FUNC_PERMISSION_DEFINITIONS
                }
                if fn not in field_map:
                    field_map[fn] = {'level': pl, 'func_permissions': dict(funcs)}
                else:
                    item = field_map[fn]
                    if pl == 0 or item['level'] == 0:
                        item['level'] = 0
                    else:
                        item['level'] = max(item['level'], pl)
                    # 功能权限按 key 取 OR：任一角色允许即允许
                    for key in FUNC_PERMISSION_DEFINITIONS:
                        item['func_permissions'][key] = bool(
                            item['func_permissions'].get(key) or funcs.get(key)
                        )
            fields = [
                {
                    'field_name': k,
                    'permission_level': v['level'],
                    'func_permissions': v['func_permissions'],
                }
                for k, v in field_map.items()
            ]

        return success_response(data={'buttons': buttons, 'fields': fields})


@extend_schema(tags=["菜单"])
class MenuExportJobViewSet(CustomExportJobViewSet):
    resource_class = MenuExportResource


@extend_schema(tags=["菜单"])
class MenuImportJobViewSet(CustomImportJobViewSet):
    resource_class = MenuImportResource

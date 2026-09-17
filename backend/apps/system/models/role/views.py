from django.db import transaction
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import error_response, success_response
from extends.drf.views_mixins import *
from .filters import RoleFilter
from .models import RoleModel
from .resources import RoleExportResource, RoleImportResource
from .serializers import RoleSerializer, RoleCreateSerializer, RoleUpdateSerializer, RoleRetrieveSerializer
from ..role_menu_button.models import RoleMenuButtonModel
from ..role_menu_field.models import RoleMenuFieldModel
from ..user.models import UserModel


@extend_schema(tags=["角色"])
class RoleViewSet(CrudViewSet, MoveMixin, BatchDestroySortMixin):
    """
    角色视图集

    N+1 查询优化：
        - retrieve 时通过 Prefetch 预加载 menu M2M 和 user M2M（含 user.dept FK），
          RoleRetrieveSerializer 的 get_menus / get_users 遍历缓存对象，
          避免 values_list() / values() 绕过 prefetch 产生额外查询。
    """

    queryset = (
        RoleModel.objects.all()
        .prefetch_related('user')
    )
    serializer_class = RoleSerializer
    retrieve_serializer_class = RoleRetrieveSerializer
    create_serializer_class = RoleCreateSerializer
    update_serializer_class = RoleUpdateSerializer
    filterset_class = RoleFilter
    export_resource_class = RoleExportResource
    import_resource_class = RoleImportResource
    search_fields = ["name", "code"]

    def retrieve(self, request, *args, **kwargs):
        """
        查询角色详情：预加载关联菜单与用户（含用户部门），
        供 RoleRetrieveSerializer.get_menus / get_users 零额外查询使用。
        """
        instance = self.get_object()
        # 重新查询并预加载 menu 和 user（含 user.dept），确保序列化器方法使用 prefetch 缓存
        instance = (
            RoleModel.objects
            .prefetch_related(
                'menu',
                Prefetch('user', queryset=UserModel.objects.select_related('dept')),
            )
            .get(pk=instance.pk)
        )
        serializer = self.get_serializer(instance)
        return success_response(message="查询详情成功", data=serializer.data)

    @extend_schema(summary="授权用户", extensions={'x-function': 'AuthorizedUser', 'x-assign_permission': False})
    @action(methods=["PUT"], detail=True)
    def authorized_user(self, request, *args, **kwargs):
        """
        批量新增和/或移除角色关联的用户（支持一次调用同时执行两种操作）：
         - add_user_ids: 要添加的用户 ID 列表（可选）
         - remove_user_ids: 要移除的用户 ID 列表（可选）

        仅管理员（超级管理员或 admin 角色）可调用，防止普通用户将自己加入任意角色提权。
        """
        # 越权防护：授权操作仅管理员可执行
        if not (request.user.is_superuser or request.user.role.filter(name='admin').exists()):
            return error_response(message="无权执行授权操作")
        role = self.get_object()
        add_user_ids = request.data.get('add_user_ids', [])
        remove_user_ids = request.data.get('remove_user_ids', [])

        with transaction.atomic():
            if add_user_ids:
                role.user.add(*add_user_ids)
            if remove_user_ids:
                role.user.remove(*remove_user_ids)
        # 重新查询并预加载关联数据，避免序列化时额外查询
        role = (
            RoleModel.objects
            .prefetch_related(
                'menu',
                Prefetch('user', queryset=UserModel.objects.select_related('dept')),
            )
            .get(pk=role.pk)
        )
        serializer = RoleRetrieveSerializer(role)
        return success_response(message="授权用户批量修改成功", data=serializer.data)

    @extend_schema(summary="授权菜单", extensions={'x-function': 'AuthorizedMenu', 'x-assign_permission': False})
    @action(methods=["PUT"], detail=True)
    def authorized_menu(self, request, *args, **kwargs):
        """
        新增或移除角色关联的菜单：
         - action：执行操作
            - add: 将 menu_id 中添加到角色
            - move: 将 menu_id 中从角色中移除
        - menu_id: 菜单 id

        仅管理员（超级管理员或 admin 角色）可调用，防止普通用户自行授权。
        """
        # 越权防护：授权操作仅管理员可执行
        if not (request.user.is_superuser or request.user.role.filter(name='admin').exists()):
            return error_response(message="无权执行授权操作")
        role = self.get_object()
        menu_id = request.data.get('menu_id')
        action_type = request.data.get('action')
        with transaction.atomic():
            if action_type == 'add':
                role.menu.add(menu_id)
            elif action_type == 'remove':
                role.menu.remove(menu_id)
                # 删除所有的按钮权限和字段权限
                RoleMenuButtonModel.objects.filter(role=role, menu_button__menu=menu_id).delete()
                RoleMenuFieldModel.objects.filter(role=role, menu_field__menu=menu_id).delete()
        # 重新查询并预加载关联数据，避免序列化时额外查询
        role = (
            RoleModel.objects
            .prefetch_related(
                'menu',
                Prefetch('user', queryset=UserModel.objects.select_related('dept')),
            )
            .get(pk=role.pk)
        )
        serializer = RoleRetrieveSerializer(role)
        return success_response(message="授权菜单修改成功", data=serializer.data)


@extend_schema(tags=["角色"])
class RoleExportJobViewSet(CustomExportJobViewSet):
    resource_class = RoleExportResource


@extend_schema(tags=["角色"])
class RoleImportJobViewSet(CustomImportJobViewSet):
    resource_class = RoleImportResource

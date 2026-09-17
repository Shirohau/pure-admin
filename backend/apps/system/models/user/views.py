import logging
from django.contrib.auth.hashers import check_password
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import success_response, error_response
from extends.drf.views_mixins import *

from ..dept.models import annotate_dept_full_path
from .filters import UserFilter
from .models import UserModel
from .resources import UserResource
from .serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer

logger = logging.getLogger(__name__)


@extend_schema(tags=["用户"])
class UserViewSet(CrudViewSet, ExportMixin, ImportMixin, BatchDestroyMixin):
    queryset = (
        UserModel.objects
        .prefetch_related('role', 'avatar')
        .select_related('dept')
    )
    serializer_class = UserSerializer
    create_serializer_class = UserCreateSerializer
    update_serializer_class = UserUpdateSerializer
    filterset_class = UserFilter
    export_resource_class = UserResource
    import_resource_class = UserResource
    search_fields = ["username", "name", "email", "mobile"]

    def get_queryset(self):
        # 如果当前用户是超级用户，则返回全部用户（不进行过滤）
        if self.request.user.is_superuser:
            return self.queryset.all()
        # 否则，过滤掉所有超级用户
        return self.queryset.filter(is_superuser=False)

    def list(self, request, *args, **kwargs):
        """
        查询用户列表，并在序列化前批量注入部门全路径缓存。

        N+1 优化说明：
            - dept_full_path 字段由 UserSerializer.get_dept_full_path 提供，
              原实现逐行调用 dept.full_path()（每个用户 1 次祖先查询）；
            - 现改为在序列化前调用 annotate_dept_full_path() 批量注入
              _dept_full_path 缓存（恒定 2 次查询，与分页大小无关），
              序列化器直接读取缓存，消除逐行祖先查询。

        Returns:
            分页列表响应，或不分页的统一成功响应
        """
        queryset = self.filter_queryset(self.get_queryset())
        # 默认启用分页，除非明确指定 paginate=false（与基类行为保持一致）
        is_paginate = request.query_params.get("paginate", "true").lower() in ("true", "1", "yes")
        if not is_paginate:
            # 禁用分页：置空分页类，走不分页分支
            self.pagination_class = None
        page = self.paginate_queryset(queryset)
        if page is not None:
            # 分页分支：批量注入部门全路径缓存后返回标准分页响应
            annotate_dept_full_path(list(page))
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # 不分页分支：批量注入部门全路径缓存后返回统一格式的成功响应
        annotate_dept_full_path(list(queryset))
        serializer = self.get_serializer(queryset, many=True)
        return success_response(message="不分页列表查询成功", data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        message = user.reset_password()
        return success_response(message=message, data=serializer.data)

    @extend_schema(summary="重置密码", extensions={'x-function': 'ResetPassword'})
    @action(methods=["PUT"], detail=True)
    def reset_password(self, request, pk):
        """
        重置用户密码，并发送新密码到邮箱

        仅管理员（超级管理员或 admin 角色）可调用，防止普通用户重置任意用户密码。
        """
        # 越权防护：仅管理员可重置他人密码
        if not (request.user.is_superuser or request.user.role.filter(name='admin').exists()):
            return error_response(message="无权重置密码")
        user = self.get_object()
        message = user.reset_password()
        serializer = self.get_serializer(user)
        return success_response(message=message, data=serializer.data)

    @extend_schema(summary="修改密码", extensions={'x-function': 'UpdatePassword'})
    @action(methods=["PUT"], detail=True)
    def update_password(self, request, *args, **kwargs):
        """密码修改（仅允许本人修改自己的密码）"""
        data = request.data
        user = self.get_object()

        # 越权防护：只允许本人修改自己的密码；
        # 管理员重置他人密码请使用 reset_password 接口
        if request.user.id != user.id:
            return error_response(message="无权修改其他用户的密码")

        old_pwd = data.get("oldPassword")
        new_pwd = data.get("newPassword")

        # 验证新密码
        if not new_pwd:
            return error_response(message="请输入新密码")

        # 如果用户旧密码为空（如新用户、第三方登录用户），则跳过旧密码验证
        if not user.password:
            # 直接修改密码
            with transaction.atomic():
                message = user.reset_password(new_password=new_pwd)
                serializer = self.get_serializer(user)
            return success_response(message=message, data=serializer.data)

        # 验证旧密码（仅当用户有旧密码时）
        if not old_pwd:
            return error_response(message="请输入旧密码")

        verify_password = check_password(old_pwd, user.password)
        if verify_password:
            with transaction.atomic():
                message = user.reset_password(new_password=new_pwd)
                serializer = self.get_serializer(user)
            return success_response(message=message, data=serializer.data)
        else:
            return error_response(message="旧密码不正确")


@extend_schema(tags=["用户"])
class UserExportJobViewSet(CustomExportJobViewSet):
    resource_class = UserResource


@extend_schema(tags=["用户"])
class UserImportJobViewSet(CustomImportJobViewSet):
    resource_class = UserResource

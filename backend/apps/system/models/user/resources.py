#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：resources.py
@Author  ：李小涛
@Date    ：2026/8/3
@Explain : 用户导入导出资源（同步/异步通用）
"""
from django.core.validators import validate_email, ValidationError
from import_export.fields import Field
from import_export.widgets import Widget, ManyToManyWidget, ForeignKeyWidget

from extends.drf.resources import CustomCeleryResource
from .filters import UserFilter
from .models import UserModel
from ..dept.models import DeptModel
from ..role.models import RoleModel


class EmailWidget(Widget):
    """邮箱校验 Widget：空值返回 None，非法格式抛出 ValueError"""

    def clean(self, value, row=None, **kwargs):
        value = (value or "").strip()
        if not value:
            return None
        try:
            validate_email(value)
        except ValidationError:
            raise ValueError("邮箱格式无效")
        return value


class UserResource(CustomCeleryResource):
    """用户导入导出资源（同步/异步通用）"""

    filterset_class = UserFilter

    username = Field(column_name="账号", attribute="username")
    name = Field(column_name="姓名", attribute="name")
    email = Field(column_name="邮箱", attribute="email", widget=EmailWidget())
    mobile = Field(column_name="电话", attribute="mobile")
    gender = Field(column_name="性别", attribute="gender")
    timezone = Field(column_name="时区", attribute="timezone")
    is_superuser = Field(column_name="超级用户", attribute="is_superuser")
    is_staff = Field(column_name="后台管理员", attribute="is_staff")
    is_active = Field(column_name="有效", attribute="is_active")
    dept = Field(
        attribute="dept",
        column_name="部门编号",
        widget=ForeignKeyWidget(DeptModel, field="code"),  # type: ignore[arg-type]
    )
    role = Field(
        attribute="role",
        column_name="角色编号",
        widget=ManyToManyWidget(RoleModel, field="code", separator="|"),  # type: ignore[arg-type]
    )

    def before_save_instance(self, instance, row, **kwargs):
        """在保存实例前设置随机默认密码（仅当未提供密码时）"""
        dry_run = kwargs.get("dry_run", False)
        if not dry_run:
            instance.set_password("admin123456")
        super().before_save_instance(instance, row, **kwargs)

    class Meta:
        model = UserModel
        fields = [
            "username", "name", "email", "mobile",
            "gender", "timezone", "is_superuser", "is_staff",
            "is_active", "dept", "role",
        ]
        import_id_fields = ("username",)
        use_bulk = False
        batch_size = 100
        skip_unchanged = True

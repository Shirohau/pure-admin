#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2025/12/1 上午10:12 
@Explain :
"""
import secrets
import string

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.contenttypes.fields import GenericRelation

from application import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.system.models import table_prefix
from extends.email.send_email.change_password import ChangePassword


def generate_random_password(length: int = 10, exclude_ambiguous: bool = True) -> str:
    """
    生成一个安全的随机密码。

    Args:
        length (int): 密码长度，默认为 10。
        exclude_ambiguous (bool): 是否排除易混淆字符（如 0/O, l/1/I），默认 True。
    """
    if length < 3:
        raise ValueError("密码长度至少为 3，以确保包含大小写字母和数字。")

    # 基础字符集
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits

    if exclude_ambiguous:
        # 移除易混淆字符
        ambiguous = "0O1lI"
        lowercase = ''.join(c for c in lowercase if c not in ambiguous)
        uppercase = ''.join(c for c in uppercase if c not in ambiguous)
        digits = ''.join(c for c in digits if c not in ambiguous)

    all_chars = lowercase + uppercase + digits

    # 确保至少包含：1个小写、1个大写、1个数字
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits)
    ]

    # 填充剩余长度
    for _ in range(length - 3):
        password.append(secrets.choice(all_chars))

    # 打乱顺序，避免固定模式
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


class UserQuerySet(models.QuerySet):
    def with_relations(self):
        """
        预加载 dept、avatar、role，避免 N+1
        """
        return self.select_related('dept').prefetch_related('avatar', 'role').filter(is_superuser=False)


class UserManager(BaseUserManager.from_queryset(UserQuerySet)):
    pass


class UserModel(AbstractUser):
    username = models.CharField(max_length=150, unique=True, db_index=True, verbose_name="账号", db_comment="账号")
    name = models.CharField(max_length=40, verbose_name="姓名", db_comment="姓名")
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True, verbose_name="邮箱", db_comment="邮箱")
    mobile = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="电话", db_comment="电话")
    avatar = GenericRelation(to="system.FileModel", verbose_name="头像", related_query_name='avatar')  # 反向查询名
    gender = models.CharField(max_length=2, null=True, blank=True, verbose_name="性别", db_comment="性别")
    timezone = models.CharField(max_length=50, default=settings.TIME_ZONE, verbose_name="时区", db_comment="时区")

    role = models.ManyToManyField(
        to="RoleModel",
        related_name="user",
        blank=True,
        db_constraint=False,
        verbose_name="关联角色"
    )
    dept = models.ForeignKey(
        to='DeptModel',
        on_delete=models.SET_NULL,
        related_name="user",
        db_constraint=False,
        null=True,
        blank=True,
        verbose_name="关联部门",
        db_comment="关联部门",
    )
    objects = UserManager()  # ← 使用自定义 Manager

    def reset_password(self, new_password=None):
        """
        重置用户密码，如果启动了邮箱，则发送邮件，如果没有，则显示给前端

        Args:
            new_password (str, optional): 新密码，不指定则自动生成
        """
        if new_password is None:
            new_password = generate_random_password()  # 或从 settings 中读取 DEFAULT_PASSWORD
        self.set_password(new_password)
        self.save(update_fields=['password'])
        if not self.email:
            return f"账号{self.username}未绑定邮箱，新密码是： {new_password}"
        # 发送邮件
        userinfo = {
            "username": self.username,
            "user_email": self.email,
            "mobile": self.mobile,
            "password": new_password,
            "name": self.name,
        }
        send_email = ChangePassword(userinfo)
        send = send_email.start()
        if not send["success"]:
            return f"{send['message']}，新密码是：{new_password}"
        return "新密码已发送至邮箱"

    class Meta:
        db_table = table_prefix + "user"
        verbose_name = "用户"
        db_table_comment = verbose_name
        verbose_name_plural = verbose_name
        ordering = ['-id']

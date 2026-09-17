#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：models.py
@Author  ：李小涛
@Date    ：2025/9/11 下午3:15
@Explain : OAuth2 第三方认证模型
"""

from django.db import models
from django.conf import settings


class UserOAuthModel(models.Model):
    """用户第三方账号绑定模型"""

    # 支持的平台列表（可根据需要扩展）
    PLATFORM_CHOICES = [
        ('weibo', '微博'),
        ('gitee', '码云'),
        ('work_weixin', '企业微信'),
        ('github', 'GitHub'),
        ('qq', 'QQ'),
        ('wechat', '微信'),
        ('alipay', '支付宝'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="user_oauth",
        on_delete=models.CASCADE,
        verbose_name="用户",
        help_text="绑定的本地用户",
        db_constraint=False,
    )
    platform = models.CharField(
        verbose_name="第三方平台",
        max_length=32,
        choices=PLATFORM_CHOICES,
        db_index=True,
        help_text="第三方平台标识"
    )
    uid = models.CharField(
        verbose_name="第三方平台用户ID",
        max_length=255,
        db_index=True,
        help_text="第三方平台的唯一用户标识"
    )
    uname = models.CharField(
        verbose_name="第三方平台用户名",
        max_length=255,
        blank=True,
        null=True,
        help_text="第三方平台显示的用户名"
    )
    uinfo = models.JSONField(
        verbose_name="第三方平台用户信息",
        default=dict,
        blank=True,
        help_text="存储第三方平台返回的完整用户信息（JSON格式）"
    )
    create_dt = models.DateTimeField(
        verbose_name="创建时间",
        db_comment="创建时间",
        auto_now_add=True,
        help_text="记录创建时间"
    )
    update_dt = models.DateTimeField(
        verbose_name="更新时间",
        db_comment="更新时间",
        auto_now=True,
        help_text="记录最后更新时间"
    )

    def __str__(self):
        return f"{self.user} - {self.get_platform_display()} - {self.uid}"

    class Meta:
        db_table = "system_user_oauth"
        verbose_name = "第三方认证"
        verbose_name_plural = verbose_name
        db_table_comment = verbose_name
        ordering = ("-id",)
        constraints = [
            models.UniqueConstraint(
                fields=['platform', 'uid'],
                name='unique_platform_uid'
            )
        ]
        indexes = [
            models.Index(fields=['user'], name='idx_user_id'),
        ]

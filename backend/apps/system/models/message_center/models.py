from django.db import models

from extends.drf.models import CustomModel
from apps.system.models import table_prefix


class MessageCenter(CustomModel):
    title = models.CharField(max_length=100, verbose_name="标题", help_text="标题")
    content = models.TextField(verbose_name="内容", help_text="内容")
    target_type = models.IntegerField(default=0, verbose_name="目标类型", help_text="目标类型")
    target_user = models.ManyToManyField(
        to='UserModel',
        related_name='message_center_user',
        through='MessageCenterTargetUser',
        through_fields=('messagecenter', 'users'),
        blank=True,
        verbose_name="目标用户",
        help_text="目标用户"
    )
    target_dept = models.ManyToManyField(
        to='DeptModel',
        blank=True,
        db_constraint=False,
        verbose_name="目标部门",
        help_text="目标部门"
    )
    target_role = models.ManyToManyField(
        to='RoleModel',
        blank=True,
        db_constraint=False,
        verbose_name="目标角色",
        help_text="目标角色"
    )

    class Meta:
        db_table = table_prefix + "message_center"
        verbose_name = "消息中心"
        verbose_name_plural = verbose_name
        ordering = ("-create_dt",)


class MessageCenterTargetUser(CustomModel):
    users = models.ForeignKey(
        to='UserModel',
        related_name="message_center_target_user",
        on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="关联用户表",
        help_text="关联用户表"
    )
    messagecenter = models.ForeignKey(
        MessageCenter,
        on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="关联消息中心表",
        help_text="关联消息中心表"
    )
    is_read = models.BooleanField(default=False, verbose_name="是否已读", help_text="是否已读")

    class Meta:
        db_table = table_prefix + "message_center_target_user"
        verbose_name = "消息中心目标用户表"
        verbose_name_plural = verbose_name

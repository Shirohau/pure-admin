#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：models.py
@Explain : 流程审核人员模型
"""
from django.conf import settings
from django.db import models

from ...models import AUDIT_STATUS, table_prefix
from ..d_flow_record.models import FlowRecord


class FlowAuditUsers(models.Model):
    """流程审核人员"""
    flow_record = models.ForeignKey(FlowRecord, db_constraint=False, on_delete=models.CASCADE)
    audit_user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='审核人', blank=True, null=True,
                                   db_constraint=False,
                                   related_name='audit_user', on_delete=models.PROTECT)
    status = models.IntegerField(choices=AUDIT_STATUS, default=0, verbose_name='状态')
    description = models.CharField(max_length=255, verbose_name="描述", null=True, blank=True, help_text="描述")
    update_datetime = models.DateTimeField(auto_now=True, null=True, blank=True, help_text="修改时间",
                                           verbose_name="修改时间")
    create_datetime = models.DateTimeField(auto_now_add=True, null=True, blank=True, help_text="创建时间",
                                           verbose_name="创建时间")

    class Meta:
        db_table = table_prefix + 'audit_users'
        verbose_name = '流程审核人员'
        verbose_name_plural = verbose_name
        ordering = ('-create_datetime',)

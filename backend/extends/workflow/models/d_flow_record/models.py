#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：models.py
@Explain : 流转记录模型
"""
from django.conf import settings
from django.db import models

from ...models import AUDIT_STATUS, table_prefix
from ..c_flow_data.models import FlowData


class FlowRecord(models.Model):
    """流转记录"""
    flow_data = models.ForeignKey(FlowData, db_constraint=False, on_delete=models.CASCADE)
    pre_user = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name='预处理人', blank=True,
                                      related_name='pre_user', db_constraint=False)
    pre_dept = models.ManyToManyField("system.DeptModel", verbose_name='预处理部门', blank=True,
                                      related_name='pre_dept', db_constraint=False)
    pre_role = models.ManyToManyField("system.RoleModel", verbose_name='预处理角色', db_constraint=False, blank=True)
    handler = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='处理人', blank=True, null=True,
                                related_name='handler', db_constraint=False,
                                on_delete=models.PROTECT)
    # 审批意见
    comment = models.TextField(verbose_name='审批意见', null=True, blank=True)
    current_node_id = models.CharField(max_length=50, verbose_name='当前节点', null=True, blank=True)
    parent_node_id = models.CharField(max_length=50, verbose_name='父节点', null=True, blank=True)
    FLOW_RECORD_TYPE = (
        ("Start", '发起节点'),
        ("Approval", '审核节点'),
        ("Gateway", '条件节点'),
        ("Cc", '抄送节点'),
    )
    type = models.CharField(choices=FLOW_RECORD_TYPE, default="", max_length=255, null=True, blank=True, verbose_name='类型')
    status = models.IntegerField(choices=AUDIT_STATUS, default=0, verbose_name='状态')
    completed_time = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    create_datetime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_datetime = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = table_prefix + 'record'
        verbose_name = '流转记录'
        verbose_name_plural = verbose_name
        ordering = ('-create_datetime',)

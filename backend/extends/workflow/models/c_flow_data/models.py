#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：models.py
@Explain : 流程数据模型
"""
from django.conf import settings
from django.db import models

from ...models import AUDIT_STATUS, table_prefix
from ..a_flow_info.models import FlowInfoModel


class FlowData(models.Model):
    """流程数据"""
    flow_info = models.ForeignKey(FlowInfoModel, db_constraint=False, verbose_name='关联流程节点表',
                                  on_delete=models.CASCADE)
    no = models.CharField(max_length=200, verbose_name='流程编号')
    name = models.CharField(max_length=100, verbose_name='名称')
    models_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='model名称')
    status = models.IntegerField(choices=AUDIT_STATUS, default=0, verbose_name='状态')
    start_user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='发起人', blank=True, null=True,
                                   related_name='start_user', db_constraint=False,
                                   on_delete=models.PROTECT)
    pre_user = models.ManyToManyField(settings.AUTH_USER_MODEL, db_constraint=False, verbose_name='预处理人',
                                      blank=True, related_name='flow_pre_user')
    pre_dept = models.ManyToManyField("system.DeptModel", db_constraint=False, verbose_name='预处理部门', blank=True,
                                      related_name='flow_pre_dept')
    pre_role = models.ManyToManyField("system.RoleModel", verbose_name='预处理角色', db_constraint=False, blank=True)
    handler = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='处理人', blank=True, null=True,
                                related_name='flow_handler', db_constraint=False,
                                on_delete=models.PROTECT)
    pre_change_content = models.JSONField(verbose_name='预改变内容', null=True, blank=True)
    # 申请表单填写的数据（动态表单提交值）
    form_data = models.JSONField(verbose_name='表单数据', null=True, blank=True)
    # 发起人自选审批人：{nodeId: [userId, ...]}
    selected_approvers = models.JSONField(verbose_name='自选审批人', null=True, blank=True)
    current_node = models.JSONField(verbose_name='当前节点', null=True, blank=True, default=dict)
    completed_time = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    create_datetime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_datetime = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = table_prefix + 'data'
        verbose_name = '流程数据'
        verbose_name_plural = verbose_name
        ordering = ('-create_datetime',)

    def generate_no(self):
        # 获取当前日期
        from django.utils import timezone
        current_date = timezone.now()

        date_str = current_date.strftime('%Y%m%d')  # 格式化日期为 YYYYMMDD
        prefix = "SH" + date_str

        # 查找当前最大编号
        max_no = FlowData.objects.filter(no__startswith=prefix).order_by('no').last()
        if max_no:
            # 解析当前最大编号的顺序部分
            last_sequence = int(max_no.no[len(prefix):])  # 获取顺序编号部分
        else:
            last_sequence = 0

        new_sequence = last_sequence + 1
        return f"{prefix}{new_sequence:06d}"  # 生成新的编号，格式为 SHYYYYMMDD000001

    def save(self, *args, **kwargs):
        if not self.no:
            # 如果没有提供 no 字段值，则自动生成
            self.no = self.generate_no()
        super().save(*args, **kwargs)

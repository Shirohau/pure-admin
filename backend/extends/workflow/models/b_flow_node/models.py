#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：models.py
@Explain : 流程节点模型
"""
from django.db import models

from ...models import table_prefix
from ..a_flow_info.models import FlowInfoModel


class FlowNode(models.Model):
    """流程节点"""
    flow_info = models.ForeignKey(FlowInfoModel, db_constraint=False, on_delete=models.CASCADE)
    node_id = models.CharField(max_length=64, verbose_name="节点ID", help_text="节点ID")
    process_index = models.IntegerField(default=0, verbose_name="索引", help_text="索引")
    name = models.CharField(max_length=64, verbose_name="节点名称", help_text="节点名称")
    # Start 开始节点
    # Approval 审批中
    # Cc 抄送
    # Gateway 节点
    node_type = models.CharField(default="Start", max_length=64, verbose_name='节点类型', help_text='节点类型')
    props = models.JSONField(null=True, blank=True, verbose_name="条件流程配置", help_text="条件流程配置")
    branch = models.JSONField(null=True, blank=True, verbose_name="分支流程配置", help_text="分支流程配置")
    is_first = models.BooleanField(default=False, verbose_name="是否首级", help_text="是否首级")
    # 子级节点
    parent = models.ForeignKey('self', null=True, blank=True, db_constraint=False, on_delete=models.CASCADE)
    create_datetime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_datetime = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = table_prefix + "node"
        verbose_name = "流程节点表"
        verbose_name_plural = verbose_name
        ordering = ('process_index',)

    @classmethod
    def save_flow_node(cls, data, flow_info_obj, parent_id=None):
        """
        保存节点数据
        """
        all_node_ids = []
        last_node_id = None
        for index, ele in enumerate(data):
            # 保存节点信息
            node_id = ele.pop('id')
            all_node_ids.append(node_id)
            flow_node_obj, _ = FlowNode.objects.update_or_create(
                flow_info=flow_info_obj, node_id=node_id, 
                defaults={
                    "name": ele.get('name'),
                    "node_type": ele.get('type'),
                    "props": ele.get('props'),
                    "branch": ele.get('branch'),
                    "process_index": index,
                    "is_first": not parent_id,
                    "parent_id": parent_id or last_node_id
                }
            )
            last_node_id = flow_node_obj.id
            # 子级节点数据保存
            branch = ele.get('props', {}).get('branch')
            if branch:
                for inx, branch_ele in enumerate(branch):
                    # Gateway下的props-branch
                    branch_node_id = branch_ele.pop('id')
                    all_node_ids.append(branch_node_id)
                    branch_flow_node_obj, _ = FlowNode.objects.update_or_create(
                        flow_info=flow_info_obj, node_id=branch_node_id,
                        defaults={
                            "name": branch_ele.get('name'),
                            "node_type": branch_ele.get('type'),
                            "props": branch_ele.get('props'),
                            "branch": branch_ele.get('branch'),
                            "process_index": inx,
                            "parent_id": flow_node_obj.id
                        })
                    # 条件分支下的各个数据保存
                    all_node_ids += cls.save_flow_node(ele.get('branch', [])[inx], flow_info_obj,
                                                        parent_id=branch_flow_node_obj.id)
        return all_node_ids

    @classmethod
    def get_flow_node(cls, flow_info_obj):
        """
        获取节点数据
        """
        data = []
        flow_node_obj = FlowNode.objects.filter(flow_info=flow_info_obj, is_first=True)
        for ele in flow_node_obj:
            data.append({
                "id": ele.node_id,
                "name": ele.name,
                "props": ele.props,
                "type": ele.node_type,
                "branch": ele.branch
            })
        return data

    @property
    def node_dict(self):
        """
        根据node_id获取节点数据
        """
        return {
            "id": self.node_id,
            "name": self.name,
            "props": self.props,
            "type": self.node_type,
            "branch": self.branch
        }

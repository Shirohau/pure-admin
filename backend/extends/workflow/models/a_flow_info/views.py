#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：views.py
@Explain : 流程信息视图集（流程设计器：保存/发布/列表/详情/软删除）

接口（前缀 /api/flow/flow-info/）：
- 列表/详情/保存/更新/软删除（ModelViewSet 默认）
- publish   发布流程（status=1，可发起）
- available 可发起流程列表（已发布且启用，同 key 多版本取最新）
- put_status 更新流程状态（1-发布 2-下架）
"""
import itertools

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from extends.drf.response import success_response, error_response
from extends.drf.views_mixins import CrudViewSet
from .models import FlowInfoModel
from .serializers import FlowInfoSerializer

@extend_schema(tags=["流程管理"])
class FlowInfoViewSet(CrudViewSet):
    """流程设计器：保存 / 发布 / 列表 / 详情 / 软删除"""
    queryset = FlowInfoModel.objects.all()
    serializer_class = FlowInfoSerializer

    @staticmethod
    def _apply_designer_data(instance, data):
        """将 AntFlow 设计器发布数据映射到 FlowInfo 字段"""
        data = data or {}
        instance.name = data.get('name') or instance.name or '未命名流程'
        instance.key = data.get('key') or instance.key
        instance.flow_code = data.get('flowCode')
        instance.group_id = data.get('groupId')
        instance.frm_type = int(data.get('frmType', 1) or 1)
        instance.frm_value = data.get('frmValue') or None
        instance.frm_url = data.get('frmUrl') or None
        instance.distinct_type = int(data.get('distinctType', 0) or 0)
        instance.is_active = bool(data.get('isActive', True))
        instance.version = str(data.get('version') or '') or None
        instance.remark = data.get('Remark')
        instance.config = data  # 完整发布数据（含 nodes 扁平数组）
        return instance

    # def create(self, request, *args, **kwargs):
    #     """保存流程（草稿，status=0）"""
    #     instance = self._apply_designer_data(FlowInfoModel(), request.data)
    #     instance.status = 0
    #     instance.save()
    #     return success_response(message="保存成功", data=FlowInfoSerializer(instance).data)
    #
    # def update(self, request, *args, **kwargs):
    #     """更新流程（草稿，status=0）"""
    #     instance = self.get_object()
    #     self._apply_designer_data(instance, request.data)
    #     instance.status = 0
    #     instance.save()
    #     return success_response(message="保存成功", data=FlowInfoSerializer(instance).data)
    #
    # def retrieve(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     return success_response(message="获取成功", data=FlowInfoSerializer(instance).data)
    #
    # def destroy(self, request, *args, **kwargs):
    #     """软删除流程"""
    #     instance = self.get_object()
    #     instance.is_deleted = True
    #     instance.save(update_fields=['is_deleted'])
    #     return success_response(message="删除成功")
    #
    # @action(methods=['post'], detail=True)
    # def publish(self, request, pk=None):
    #     """发布流程（status=1，可发起）"""
    #     instance = self.get_object()
    #     if request.data:
    #         self._apply_designer_data(instance, request.data)
    #     nodes = (instance.config or {}).get('nodes') or []
    #     if not nodes:
    #         return error_response(message="流程未配置节点，无法发布")
    #     instance.status = 1
    #     instance.save()
    #     return success_response(message="发布成功", data=FlowInfoSerializer(instance).data)
    #
    # @action(methods=['get'], detail=False)
    # def available(self, request):
    #     """可发起流程列表（已发布且启用，同一流程 key 多版本只取最新一条）"""
    #     qs = self.filter_queryset(self.get_queryset().filter(status=1, is_active=True))
    #     # 按 key 分组取最新版本（key 为设计器生成的流程唯一标识）
    #     ordered = qs.order_by('key', '-id')
    #     latest_ids = [next(g).id for _, g in itertools.groupby(ordered, key=lambda x: x.key)]
    #     qs = qs.filter(id__in=latest_ids)
    #     page = self.paginate_queryset(qs)
    #     if page is not None:
    #         serializer = FlowInfoSerializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)
    #     serializer = FlowInfoSerializer(qs, many=True)
    #     return success_response(data=serializer.data)
    #
    # @action(methods=['put'], detail=True)
    # def put_status(self, request, pk=None):
    #     """更新流程状态（1-发布 2-下架）"""
    #     instance = self.get_object()
    #     status_value = request.data.get('status')
    #     if status_value is None:
    #         return error_response(message="状态值不能为空")
    #     status_value = int(status_value)
    #     if status_value == 1:
    #         nodes = (instance.config or {}).get('nodes') or []
    #         if not nodes:
    #             return error_response(message="流程未配置节点，无法发布")
    #     instance.status = status_value
    #     instance.save(update_fields=['status', 'update_datetime'])
    #     return success_response(message="状态更新成功", data=FlowInfoSerializer(instance).data)

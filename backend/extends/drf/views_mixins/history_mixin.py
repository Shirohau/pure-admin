#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：history_mixin.py
@Author  ：李小涛
@Date    ：2025/11/29 上午10:53 
@Explain : 历史记录混入（基于 django-simple-history）
"""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import action

from extends.drf.response import success_response

# 历史变更类型符号 → 中文描述映射
HISTORY_TYPE_CHOICES = {"+": "新增", "~": "修改", "-": "删除"}


class HistorySerializer(serializers.Serializer):
    """
    历史记录序列化类：
    输出历史记录的 id、变更时间、变更者、变更类型及变更字段明细。
    """

    history_id = serializers.IntegerField(label="历史记录id")
    history_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", label="变更时间")
    history_user = serializers.StringRelatedField(label="变更者")
    history_user_name = serializers.SerializerMethodField(label="变更者名称")
    history_type = serializers.SerializerMethodField(label="变更类型")
    changed_fields = serializers.SerializerMethodField(label="变更字段")

    def get_history_user_name(self, instance) -> str | None:
        """获取变更者名称（用户可能已被删除，需判空处理）"""
        return instance.history_user.name if instance.history_user else None

    def get_history_type(self, instance) -> str:
        """将历史类型符号（+ / ~ / -）转换为中文描述"""
        return HISTORY_TYPE_CHOICES[instance.history_type]

    def get_changed_fields(self, instance) -> dict:
        """
        计算当前版本相对上一版本的字段变更明细

        实现说明：
        - 通过 diff_against 获取与上一版本的差异；
        - 上一版本优先从 context 中预加载的 prev_map 获取，避免 N+1 查询；
        - 如果是第一个历史记录（无上一版本），则返回空字典；
        - 差异字段使用模型的 verbose_name 作为展示名。

        Args:
            instance: 历史记录实例

        Returns:
            {字段展示名: {"old": 旧值, "new": 新值}} 字典
        """
        prev_map = self.context.get("prev_map", {})
        prev_record = prev_map.get(instance.pk)  # 使用预加载的 prev_map，不再查 DB
        if not prev_record:
            # 首次创建：无上一版本，返回空
            return {}
        # 获取原始模型类（用于字段 verbose_name 展示）
        model_class = instance.instance_type
        # 计算与上一版本的差异（排除 updater 字段）
        diff_result = instance.diff_against(prev_record, excluded_fields=("updater",))
        changes = {}
        for change in diff_result.changes:
            field_name = change.field
            model_field = model_class._meta.get_field(field_name)
            display_name = getattr(model_field, "verbose_name", field_name)
            changes[display_name] = {
                "old": change.old,
                "new": change.new,
            }
        return changes


class HistoryMixin:
    """
    历史记录混入：
        - history_list: 查询单个对象的所有历史记录（含变更字段明细）
        - history_recover: 恢复到指定历史版本
    使用前提：模型已接入 django-simple-history。
    """

    @extend_schema(summary="历史记录", extensions={"x-function": "HistoryList", "x-assign_permission": False})
    @action(methods=["GET"], detail=True)
    def history_list(self, request, *args, **kwargs):
        """
        查询单个对象的所有历史记录

        实现说明：
        - 禁用数据过滤（extra_filter_class），确保有权限访问该对象的用户都能查看历史；
        - 先按时间升序构建 prev_map（当前记录 → 时间上紧邻的更早版本），
          供序列化时计算变更字段明细；
        - 分页查询按时间降序（新 → 旧），符合用户浏览习惯。

        Args:
            request: 请求对象，kwargs 含对象主键

        Returns:
            分页历史记录响应，或不分页的统一成功响应
        """
        self.extra_filter_class = []  # 禁用数据过滤
        instance = self.get_object()

        # Step 1: 获取所有历史记录，按时间升序（旧 → 新），用于构建正确的 prev_map
        history_asc = instance.history.all().select_related("history_user").order_by("history_date")
        history_list = list(history_asc)  # 强制加载到内存

        # Step 2: 构建 prev_map —— 当前记录 ID -> 时间上紧邻的上一个版本（更早的）
        prev_map = {}
        for index in range(1, len(history_list)):
            prev_map[history_list[index].pk] = history_list[index - 1]

        # Step 3: 分页用的 queryset 必须是降序（新 → 旧），符合用户预期
        history_desc = instance.history.all().select_related("history_user").order_by("-history_date")
        page = self.paginate_queryset(history_desc)

        if page is not None:
            serializer = HistorySerializer(page, many=True, context={"prev_map": prev_map})
            return self.get_paginated_response(serializer.data)

        serializer = HistorySerializer(history_desc, many=True, context={"prev_map": prev_map})
        return success_response(message="不分页历史记录列表", data=serializer.data)

    @extend_schema(summary="恢复记录", extensions={"x-function": "HistoryRecover"})
    @action(methods=["POST"], detail=True)
    def history_recover(self, request, *args, **kwargs):
        """
        恢复指定的历史记录

        请求体格式：{"history_id": 123}

        实现说明：
        从历史记录中取出该版本的数据快照（history.instance），
        重新保存为一条新记录（即用历史数据覆盖当前数据）。

        Args:
            request: 请求对象，body 需携带 history_id，kwargs 含对象主键

        Returns:
            统一成功响应（含恢复后的数据）
        """
        history_id = request.data.get("history_id")
        instance = self.get_object()
        history = instance.history.get(history_id=history_id)
        recovered_instance = history.instance
        recovered_instance.save()
        serializer = self.get_serializer(recovered_instance)
        return success_response(message="恢复记录成功", data=serializer.data)

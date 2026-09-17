#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：batch_update_mixin.py
@Author  ：李小涛
@Date    ：2026/9/10 上午10:00 
@Explain : 批量更新混入
"""
import logging

from django.core.exceptions import FieldDoesNotExist
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from simple_history.utils import bulk_update_with_history

from extends.drf.response import success_response, error_response

logger = logging.getLogger(__name__)


class BatchUpdateMixin:
    """
    批量更新混入：
    通过 POST 请求传入 ids 列表与待更新数据，一次请求批量更新对应记录。
    使用前提：模型存在主键 id 字段；视图可配置 update_serializer_class（缺省回退 serializer_class）。

    实现说明：待更新数据统一经序列化器局部校验一次，再通过 bulk_update 一次性写库，
    不再逐条循环更新；模型配置了历史记录（history 属性）时改用 bulk_update_with_history
    同步生成历史记录，并统一填充审计字段（updater / update_dt）。
    """

    @extend_schema(summary="批量更新", extensions={"x-function": "BatchUpdate"})
    @action(methods=["post"], detail=False)
    @transaction.atomic
    def batch_update(self, request, *args, **kwargs):
        """
        根据 ids 批量更新数据

        请求体格式：{"ids": [1, 2, 3], "data": {"status": "已通过"}}

        处理流程：
            1. 校验 ids 与 data 参数（缺失或为空时直接返回错误）；
            2. 先经过过滤器过滤（如数据权限），再按 id 筛选出可更新记录；
            3. 待更新数据统一经序列化器局部校验一次；
            4. 校验数据写入各实例后，使用 bulk_update 一次性写库；
               模型存在历史记录时改用 bulk_update_with_history，同步生成历史记录。

        Args:
            request: 请求对象，body 中必须携带 ids 列表与 data 对象

        Returns:
            - 成功：批量更新成功响应（含更新条数）
            - 缺少参数 / 无可更新数据 / 含不支持批量更新的字段：错误响应
        """
        ids = request.data.get("ids")
        data = request.data.get("data")
        if not ids:
            return error_response(message="未获取到 ids 字段")
        if not isinstance(data, dict) or not data:
            return error_response(message="未获取到 data 字段或格式错误")

        # 先经过过滤器过滤（如数据权限），再按 id 筛选可更新记录
        queryset = self.filter_queryset(self.get_queryset()).filter(id__in=ids)
        instances = list(queryset)
        if not instances:
            return error_response(message="未找到可更新的数据")
        model = queryset.model

        # 更新序列化类：优先使用 update_serializer_class，缺省回退 serializer_class
        serializer_class = getattr(self, "update_serializer_class", None) or self.serializer_class

        # 统一局部校验一次待更新数据，不再逐条实例化序列化器
        serializer = serializer_class(data=data, partial=True, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # 收集批量更新字段：仅支持模型具体字段（外键可更新），多对多等关联字段无法批量写库
        update_fields = []
        for field_name in validated_data:
            # 兼容外键的 xxx_id 字段写法（如 updater_id → updater）
            candidates = (field_name, field_name[:-3]) if field_name.endswith("_id") else (field_name,)
            field = None
            for candidate in candidates:
                try:
                    field = model._meta.get_field(candidate)
                    break
                except FieldDoesNotExist:
                    continue
            if field is None or not field.concrete or field.many_to_many or field.primary_key:
                return error_response(message=f"字段 {field_name} 不支持批量更新")
            if field.name not in update_fields:
                update_fields.append(field.name)

        # 审计字段：data 未显式提供 updater 时填充为当前用户，更新时间统一刷新
        # 说明：bulk_update 不会触发 auto_now 与序列化器 update()，需手动填充
        user = request.user if request.user.is_authenticated else None
        fill_updater = user and "updater" not in update_fields
        if fill_updater:
            update_fields.append("updater")
        if "update_dt" not in update_fields:
            update_fields.append("update_dt")
        now = timezone.now()

        # 校验数据写入各实例（仅内存赋值，最终一次性批量写库）
        for instance in instances:
            for field_name, value in validated_data.items():
                setattr(instance, field_name, value)
            if fill_updater:
                instance.updater = user
            instance.update_dt = now

        # 批量写库：模型存在历史记录时改用 bulk_update_with_history 同步生成历史
        if hasattr(model, "history"):
            bulk_update_with_history(instances, model, fields=update_fields, default_user=user)
        else:
            model._default_manager.bulk_update(instances, fields=update_fields)

        return success_response(
            message=f"批量更新成功，共{len(instances)}条",
            data={"updated_count": len(instances)},
        )

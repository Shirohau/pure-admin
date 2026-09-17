#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：batch_destroy_sort_mixin.py
@Author  ：李小涛
@Date    ：2025/12/27 下午2:05 
@Explain : 带排序重置的批量删除混入
"""
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import error_response, success_response


class BatchDestroySortMixin:
    """
    批量删除并重新排序混入：
    删除指定 ID 的对象后，自动调整剩余对象的排序值（sort 字段），
    确保排序值保持连续性。整个操作在事务中执行，保证数据一致性。
    使用前提：模型存在 id 与 sort 字段。
    """

    @extend_schema(summary="批量删除", extensions={"x-function": "BatchDestroy"})
    @action(methods=["delete"], detail=False)
    @transaction.atomic
    def batch_destroy(self, request, *args, **kwargs):
        """
        批量删除对象并重新排序

        请求体格式：{"ids": [1, 2, 3]}

        处理流程：
            1. 校验 ids 参数；
            2. 找到待删除对象中最小的 sort 值，作为重排的起始值；
            3. 批量删除指定对象（QuerySet.delete 不触发模型 delete 方法）；
            4. 将 sort 值大于等于起始值的剩余对象，按原顺序重新分配连续的 sort 值。

        Args:
            request: 请求对象，body 中必须携带 ids 列表

        Returns:
            - 成功：批量删除成功响应
            - 缺少 ids：错误响应
        """
        ids = request.data.get("ids")
        if not ids:
            return error_response(message="未获取到 ids 字段")

        queryset = self.get_queryset()
        # 获取待删除对象中最小的排序值（作为重排的起始值）
        first_to_delete = queryset.filter(id__in=ids).order_by("sort").first()
        # 边界处理：ids 全部不存在（已被他人删除或无效）时直接返回，避免空值异常
        if first_to_delete is None:
            return error_response(message="未找到匹配的删除记录")
        min_deleted_sort = first_to_delete.sort

        # 批量删除对象（QuerySet.delete 不触发模型 delete 方法）
        queryset.filter(id__in=ids).delete()

        # 获取所有剩余的、sort >= min_deleted_sort 的对象，按原 sort 排序
        remaining_objects = (
            queryset.filter(sort__gte=min_deleted_sort)
            .order_by("sort")  # 按原顺序排，保证重排后逻辑一致
        )

        # 重新分配连续的 sort 值，从 min_deleted_sort 开始
        new_sort = min_deleted_sort
        for obj in remaining_objects:
            if obj.sort != new_sort:
                obj.sort = new_sort
                obj.save(update_fields=["sort"])
            new_sort += 1

        return success_response(message="批量删除成功")

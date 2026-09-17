#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：batch_destroy_mixin.py
@Author  ：李小涛
@Date    ：2025/12/27 下午2:04 
@Explain : 批量删除混入（不含排序处理）
"""
import logging

from django.db.models.deletion import ProtectedError
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import success_response, error_response

logger = logging.getLogger(__name__)


class BatchDestroyMixin:
    """
    批量删除混入：
    通过 DELETE 请求传入 ids 列表，批量删除对应的数据记录。
    使用前提：模型存在主键 id 字段。
    """

    @extend_schema(summary="批量删除", extensions={"x-function": "BatchDestroy"})
    @action(methods=["delete"], detail=False)
    def batch_destroy(self, request, *args, **kwargs):
        """
        根据 ids 批量删除数据

        请求体格式：{"ids": [1, 2, 3]}

        处理流程：
            1. 校验 ids 参数（缺失或为空时直接返回错误）；
            2. 先经过过滤器过滤（如数据权限），再按 id 批量删除；
            3. 捕获 ProtectedError，返回友好的错误提示。

        Args:
            request: 请求对象，body 中必须携带 ids 列表

        Returns:
            - 成功：批量删除成功响应
            - 缺少 ids：错误响应
            - 存在受保护的外键引用：错误响应
        """
        ids = request.data.get("ids")
        if not ids:
            return error_response(message="未获取到 ids 字段")

        # 先经过过滤器过滤（如数据权限），再按 id 批量删除
        queryset = self.filter_queryset(self.get_queryset())
        try:
            queryset.filter(id__in=ids).delete()
        except ProtectedError as e:
            logger.warning("批量删除失败，存在受保护的外键引用: %s", e)
            return error_response(
                message="批量删除失败，部分数据被其他记录引用，请先解除关联后再删除",
                data=str(e),
            )
        return success_response(message="批量删除成功")

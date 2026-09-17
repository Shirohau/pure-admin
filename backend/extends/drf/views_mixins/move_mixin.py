#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：move_mixin.py
@Author  ：李小涛
@Date    ：2025/12/27 下午2:03 
@Explain : 上移/下移混入
"""
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import error_response, success_response


class MoveMixin:
    """
    上移/下移混入：
    通过 GET 请求传入 direction 参数（up / down）移动对象的排序位置。
    使用前提：模型需实现 move_up() / move_down() 方法（如 treebeard 节点）。
    """

    @extend_schema(summary="移动", extensions={"x-function": "Move"})
    @action(methods=["GET"], detail=True)
    def move(self, request, *args, **kwargs):
        """
        移动对象

        请求参数：?direction=up 表示上移，?direction=down 表示下移

        Args:
            request: 请求对象，query_params 需携带 direction，kwargs 含对象主键

        Returns:
            - 移动成功：成功响应
            - 已到顶/底：错误响应
            - 无效方向：错误响应
        """
        instance = self.get_object()
        direction = request.query_params.get("direction")
        # 合法的移动方向 → 对应执行方法的映射
        direction_handlers = {
            "up": instance.move_up,
            "down": instance.move_down,
        }

        if direction not in direction_handlers:
            return error_response(message="无效的移动方向，请传入 'up' 或 'down'。")

        # 执行对应方向的移动操作
        move_func = direction_handlers[direction]
        if move_func():
            return success_response(message="移动成功")
        return error_response(message="当前项已到顶/底")

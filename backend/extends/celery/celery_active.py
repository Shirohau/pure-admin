#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：celery_active.py
@Author  ：李小涛
@Date    ：2025/11/30 下午3:17 
@Explain :
"""

from celery import current_app
from functools import wraps

from extends.drf.response import error_response


def is_celery_active() -> bool:
    """
    检查是否有活跃的 Celery Worker。
    返回 True 表示至少有一个 Worker 在线并可接收任务。
    """
    try:
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        return bool(active_workers and len(active_workers) > 0)
    except Exception as e:
        # 如果连接失败（如Redis认证错误），认为Celery不活跃
        print(f"Celery connection error: {e}")
        return False


def require_celery_active(view_method):
    """
    装饰器：仅当 Celery Worker 在线时才允许执行视图方法，
    否则返回错误响应。
    """

    @wraps(view_method)
    def wrapper(self, *args, **kwargs):
        if not is_celery_active():
            return error_response(message="Celery 服务未启动，请使用同步接口")
        return view_method(self, *args, **kwargs)

    return wrapper

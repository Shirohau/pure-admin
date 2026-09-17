#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：routing.py.py
@Author  ：李小涛
@Date    ：2025/12/1 下午1:16 
@Explain :  WebSocket 路由配置
"""
""""""
from django.urls import re_path
from .views import InfraConsumer

websocket_urlpatterns = [
    re_path(r"^ws/?$", InfraConsumer.as_asgi()),
]

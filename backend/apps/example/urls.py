#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：urls.py
@Author  ：李小涛
@Date    ：2025/11/26 下午3:25 
@Explain : example 示例应用 统一管理路由
"""

from django.urls import path, include

urlpatterns = [
    path('', include('apps.example.models.publisher.urls')),
    path('', include('apps.example.models.author.urls')),
    path('', include('apps.example.models.book.urls')),
]

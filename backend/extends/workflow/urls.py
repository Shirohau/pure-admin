#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：urls.py
@Explain : 审批流 统一管理路由（接口前缀 /api/flow/）
"""

from django.urls import path, include

urlpatterns = [
    path('', include('extends.workflow.models.a_flow_info.urls')),
]

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：urls.py
@Author  ：李小涛
@Date    ：2026/6/3 
@Explain : 验证码路由配置
"""
from django.urls import path, include
from rest_framework import routers
from .views import OTPView

router = routers.DefaultRouter()
router.register(r'otp', OTPView, basename='otp')

urlpatterns = [
    path('', include(router.urls)),
]

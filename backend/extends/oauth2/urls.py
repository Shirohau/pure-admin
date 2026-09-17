#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：urls.py
@Author  ：李小涛
@Date    ：2025/12/1 下午8:33 
@Explain : OAuth2 路由配置
"""
from django.urls import path, include

from rest_framework import routers
from .views import UserOAuthView

router = routers.DefaultRouter()
router.register(r'oauth2', UserOAuthView, basename='oauth2')

urlpatterns = [
    path('', include(router.urls)),
]

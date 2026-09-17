#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：urls.py
@Author  ：李小涛
@Date    ：2025/11/26 下午5:35 
@Explain : 图书 路由
"""

from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'book/async_import', BookImportJobViewSet)
router.register(r'book/async_export', BookExportJobViewSet)
router.register(r'book', BookViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

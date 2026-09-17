#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：urls.py
@Author  ：李小涛
@Date    ：2025/11/26 上午11:44 
@Explain :
"""

from django.urls import path

from drf_spectacular.views import SpectacularSwaggerView, SpectacularRedocView, SpectacularJSONAPIView

urlpatterns = [
    # json 格式的路由
    path('doc/json/', SpectacularJSONAPIView.as_view(), name='schema-json'),
    # swagger-ui的路由
    # path('doc/ui/', SpectacularSwaggerView.as_view(url_name='schema-json'), name='swagger-ui'),
    path('', SpectacularSwaggerView.as_view(url_name='schema-json'), name='swagger-ui'),
    # redoc的路由
    path('doc/redoc/', SpectacularRedocView.as_view(url_name='schema-json'), name='swagger-redoc'),
]

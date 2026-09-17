#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：urls.py
@Author  ：李小涛
@Date    ：2025/12/2 下午4:09 
@Explain :
"""
from django.urls import path, include

urlpatterns = [
    path('', include('apps.system.models.api_white.urls')),
    path('', include('apps.system.models.area.urls')),
    path('', include('apps.system.models.dept.urls')),
    path('', include('apps.system.models.dictionary.urls')),
    path('', include('apps.system.models.role.urls')),
    path('', include('apps.system.models.user.urls')),
    path('', include('apps.system.models.file.urls')),
    path('', include('apps.system.models.export_field_template.urls')),
    path('', include('apps.system.models.log_export.urls')),
    path('', include('apps.system.models.log_import.urls')),
    path('', include('apps.system.models.log_login.urls')),
    path('', include('apps.system.models.log_request.urls')),
    path('', include('apps.system.models.menu.urls')),
    path('', include('apps.system.models.menu_button.urls')),
    path('', include('apps.system.models.menu_field.urls')),
    path('', include('apps.system.models.role_menu_button.urls')),
    path('', include('apps.system.models.role_menu_field.urls')),
    path('', include('apps.system.models.config.urls')),
    path('', include('apps.system.models.message_center.urls')),
    # path('', include('apps.system.models.oauth2.urls')),
]

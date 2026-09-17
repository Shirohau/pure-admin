#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/11/28 下午5:34 
@Explain : 性能优化
"""

from application import settings

# ********** 注册路由 **********
settings.PLUGINS_URL_PATTERNS += [{"path": r'__debug__/', "include": "debug_toolbar.urls"}]

# ******** 注册中间件 **********
settings.MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# ********** 注册APP **********
settings.INSTALLED_APPS += ['debug_toolbar']

# 允许显示工具栏的 IP 地址（开发时通常允许所有）
INTERNAL_IPS = ['127.0.0.1', ]

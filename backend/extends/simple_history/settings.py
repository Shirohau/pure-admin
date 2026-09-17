#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/11/29 上午7:39 
@Explain : 历史记录
"""
from application import settings

# ********** 注册APP **********
settings.INSTALLED_APPS += ['simple_history']

# ********** 注册中间件 **********
settings.MIDDLEWARE += ['simple_history.middleware.HistoryRequestMiddleware']

# ********** 注册路由 **********
# settings.PLUGINS_URL_PATTERNS += [{"path": r'api/auth/', "include": "rest_framework.urls"}]

# ********** 注册配置 **********

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/11/26 上午11:00 
@Explain : example 配置文件
"""

from application import settings

# ********** 注册路由 **********
settings.PLUGINS_URL_PATTERNS += [{"path": r'api/example/', "include": "apps.example.urls"}]

# ******** 注册中间件 **********
settings.MIDDLEWARE += []

# ********** 注册APP **********
settings.INSTALLED_APPS += ['example']


#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/11/28 下午4:55 
@Explain : django-silk 性能优化配置
"""

from application import settings

# ********** 注册路由 **********
settings.PLUGINS_URL_PATTERNS += [{"path": r'silk/', "include": "silk.urls"}]

# ******** 注册中间件 **********
settings.MIDDLEWARE.insert(0, 'silk.middleware.SilkyMiddleware')

# ********** 注册APP **********
settings.INSTALLED_APPS += ['silk']

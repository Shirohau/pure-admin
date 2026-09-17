#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：setting.py
@Author  ：李小涛
@Date    ：2025/10/27 下午1:19 
@Explain :
"""

from application import settings

# ********** 注册APP **********
settings.INSTALLED_APPS += ['corsheaders']

# ********** 注册中间件 **********
# settings.MIDDLEWARE += []
# 这个中间件需要放在第一位
settings.MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')

# ********** 注册路由 **********
# settings.PLUGINS_URL_PATTERNS += [{"path": r'api/auth/', "include": "rest_framework.urls"}]

# ********** 注册配置 **********

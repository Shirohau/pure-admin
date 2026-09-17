#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py.py
@Author  ：李小涛
@Date    ：2025/11/29 下午12:31 
@Explain : 导入导出 配置
"""

from application import settings

# ********** 注册APP **********
settings.INSTALLED_APPS += ['import_export', 'import_export_extensions']

# ********** 注册中间件 **********
# settings.MIDDLEWARE += []

# ********** 注册路由 **********
# settings.PLUGINS_URL_PATTERNS += [{"path": r'api/auth/', "include": "rest_framework.urls"}]

# ********** 注册配置 **********
IMPORT_EXPORT_USE_TRANSACTIONS = True  # 在数据导入中使用数据库事务，以确保安全
IMPORT_EXPORT_IMPORT_IGNORE_BLANK_LINES = True  # 在导入Excel时，忽略空行

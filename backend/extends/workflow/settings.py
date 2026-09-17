#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/12/29 上午8:36
@Explain : 审批流配置
"""

from application import settings

# ********** 注册路由 **********
settings.PLUGINS_URL_PATTERNS += [{"path": r'api/workflow/', "include": "extends.workflow.urls"}]

# ******** 注册中间件 **********
settings.MIDDLEWARE += []

# ********** 注册APP **********
settings.INSTALLED_APPS += ["extends.workflow", ]

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/12/2 下午4:09 
@Explain :
"""
from application import settings

# ********** 注册路由 **********
settings.PLUGINS_URL_PATTERNS += [{"path": r'api/system/', "include": "apps.system.urls"}]

# ******** 注册中间件 **********
settings.MIDDLEWARE += [
    'apps.system.models.user.middleware.UserTimezoneMiddleware',
    'apps.system.models.log_request.middleware.RequestLogMiddleware'
]

# ********** 注册APP **********
settings.INSTALLED_APPS += ['system', 'treebeard']
# 自定义用户模型
AUTH_USER_MODEL = "system.UserModel"
# 部门模型
DEPT_MODEL = "system.DeptModel"

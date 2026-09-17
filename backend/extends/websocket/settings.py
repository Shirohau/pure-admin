#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/12/1 上午11:50 
@Explain :
"""
from application import settings

# ********** 注册APP **********
settings.INSTALLED_APPS += ['channels']

# ********** 注册中间件 **********
# settings.MIDDLEWARE += []

# ********** 注册路由 **********
# settings.PLUGINS_URL_PATTERNS += [{"path": r'api/auth/', "include": "rest_framework.urls"}]

# ********** 注册配置 **********
# 配置Redis通道层
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        "CONFIG": {
            "hosts": ["redis://127.0.0.1:6379/3"],  # Redis地址
        },
    },
}
DEFAULT_GROUP_NAME = "dvud_group"  # 通道默认组名

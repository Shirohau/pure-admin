#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：env_dev.py
@Author  ：李小涛
@Date    ：2025/11/26 上午9:06 
@Explain : 开发环境配置文件
"""
# 开启调试模式
DEBUG = True
# 允许所有域名可以访问服务器
ALLOWED_HOSTS = ["*"]
# 允许所有前端域名跨域访问
CORS_ALLOW_ALL_ORIGINS = True

# ================================================= #
# **************** mysql数据库 配置  **************** #
# ================================================= #
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "db_name",
        "USER": "root",
        "PASSWORD": "123456",
        "HOST": "127.0.0.1",
        "PORT": 3306,
        "OPTIONS": {"charset": "utf8mb4"},
    },
}

# ================================================= #
# ****************** redis配置，  ****************** #
# ================================================= #
REDIS_PASSWORD = "123456"  # 如果Redis没有设置密码，请留空
REDIS_HOST = "127.0.0.1"
REDIS_URL = f"redis://:{REDIS_PASSWORD or ""}@{REDIS_HOST}:6379"

from extends.silk.settings import *  # silk 性能优化
from extends.debug_toolbar.settings import *  # debug_toolbar 性能优化

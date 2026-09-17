#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：env_prod.py
@Author  ：李小涛
@Date    ：2025/11/26 上午9:08 
@Explain : 生产环境配置文件
"""
import os

# 关掉调试模式
DEBUG = False
# 允许指定域名可以访问服务器
ALLOWED_HOSTS = ["127.0.0.1", "localhost", os.environ.get("PUBLIC_IP"), os.environ.get("ADMIN_URL")]
# # 允许指定前端域名跨域访问
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8080",
    f"http://{os.environ.get('ADMIN_URL')}",
    f"https://{os.environ.get('ADMIN_URL')}"
]

# ================================================= #
# **************** mysql数据库 配置  **************** #
# ================================================= #
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("MYSQL_DATABASE"),
        "USER": "root",
        "PASSWORD": os.environ.get("MYSQL_PASSWORD"),
        "HOST": "mysql",
        "PORT": 3306,
        "OPTIONS": {"charset": "utf8mb4"},
    },
}

# ================================================= #
# ****************** redis配置，  ****************** #
# ================================================= #
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_HOST = "redis"
REDIS_URL = f"redis://:{REDIS_PASSWORD or ''}@{REDIS_HOST}:6379"

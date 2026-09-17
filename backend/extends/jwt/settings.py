#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/11/27 上午10:05 
@Explain : simplejwt 插件配置：注册应用、挂载路由、配置 DRF 认证与 JWT 参数
"""
from datetime import timedelta

from application import settings

# ********** 注册 APP **********
# 启用 token 黑名单应用（踢用户下线、刷新轮换时拉黑旧 token 依赖该应用）
settings.INSTALLED_APPS += ["rest_framework_simplejwt.token_blacklist"]

# ********** 注册路由 **********
# 将 jwt 模块的 URL 挂载到项目统一插件路由中
settings.PLUGINS_URL_PATTERNS += [{"path": r'', "include": "extends.jwt.urls"}]

# ******** 修改DRF配置 ********
# 将 simplejwt 认证器插入到认证链最前面（自定义认证器保持原有顺序不变）
custom_auth = ('rest_framework_simplejwt.authentication.JWTAuthentication',)
existing = settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']
settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = custom_auth + tuple(existing)

# ********** simplejwt配置 **********
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),  # 访问 token 有效期（开发调试时可临时改为 seconds=10）
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # 刷新令牌有效期
    'AUTH_HEADER_TYPES': ('Bearer',),  # Authorization 请求头前缀，默认 Bearer
    'UPDATE_LAST_LOGIN': True,  # 登录时更新用户最后登录时间

    # === 黑名单 / 轮换机制 ===
    'ROTATE_REFRESH_TOKENS': True,          # 刷新 token 时生成新的 refresh token
    'BLACKLIST_AFTER_ROTATION': True,       # 刷新后旧 refresh token 自动加入黑名单
    'ALGORITHM': 'HS256',                   # 签名算法（显式指定，避免依赖默认值）
}

"""
补充说明：Access Token 无法被直接拉黑
SimpleJWT 的黑名单机制只针对 Refresh Token。
如果需要立即吊销 Access Token，需自行实现基于 Redis + jti 的中间件校验。
"""
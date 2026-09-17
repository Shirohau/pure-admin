#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：urls.py
@Author  ：李小涛
@Date    ：2025/11/27 上午10:09 
@Explain : jwt 模块路由：登录、刷新、验证、在线用户、踢用户下线
"""
from django.urls import path

from .views import (
    CustomTokenBlacklistView,
    CustomTokenObtainPairView,
    CustomTokenOnlineView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
)

urlpatterns = [
    # 登录：用户名/邮箱/手机号 + 密码换取 token
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # 刷新：用 refresh token 换取新的 access token
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    # 验证：校验 access token 有效性
    path('api/token/verify/', CustomTokenVerifyView.as_view(), name='token_verify'),
    # 在线用户：查询未过期的登录会话列表
    path('api/token/online/', CustomTokenOnlineView.as_view(), name='token_online'),
    # 踢下线：管理员将指定用户的所有会话加入黑名单
    path('api/token/blacklist/', CustomTokenBlacklistView.as_view(), name='token_blacklist'),
]

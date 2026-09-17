#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：middleware.py
@Author  ：李小涛
@Date    ：2025/12/1 上午11:05 
@Explain : 为用户设置不同时区
"""

import pytz
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication


class UserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 尝试从 JWT 中获取用户
        try:
            jwt_auth = JWTAuthentication()
            user_auth = jwt_auth.authenticate(request)
            if user_auth is not None:
                user, _ = user_auth
                if hasattr(user, 'timezone') and user.timezone:
                    tz = pytz.timezone(user.timezone)
                    timezone.activate(tz)
                else:
                    timezone.deactivate()
            else:
                timezone.deactivate()
        except Exception:
            # 如 token 无效、过期等，视为匿名用户
            timezone.deactivate()

        response = self.get_response(request)
        return response

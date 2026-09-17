#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：apps.py
@Author  ：李小涛
@Date    ：2026/6/3 
@Explain : 验证码应用配置
"""

from django.apps import AppConfig


class VerificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'extends.otp'
    verbose_name = '一次性密码'

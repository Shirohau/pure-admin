#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/12/29 上午8:36
@Explain : 配置邮箱
"""

# 是否启用邮件功能
ENABLE_EMAIL = True
# 使用SMTP协议来发送邮件
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# ================================================= #
# ****************** 邮件SMTP配置  ****************** #
# ================================================= #

# 多邮箱配置 - 可以配置多个邮箱账户
EMAIL_ACCOUNTS = {
    # 默认邮箱（必须存在）
    'default': {
        'EMAIL_HOST': "smtp.qq.com",  # 发送邮件服务器
        'EMAIL_PORT': 587,  # 邮件服务器端口
        'EMAIL_USE_TLS': True,  # 使用 TLS 加密
        'EMAIL_HOST_USER': "",  # 发件邮箱
        'EMAIL_HOST_PASSWORD': "",  # 发件邮箱授权码
        'DEFAULT_FROM_EMAIL': "",  # 发件人
    },

    # 可以添加更多邮箱账户
    # 'work': {
    #     'EMAIL_HOST': "smtp.company.com",
    #     'EMAIL_PORT': 587,
    #     'EMAIL_USE_TLS': True,
    #     'EMAIL_HOST_USER': "work@company.com",
    #     'EMAIL_HOST_PASSWORD': "work_password",
    #     'DEFAULT_FROM_EMAIL': "Company <work@company.com>",
    # },

    # 'personal': {
    #     'EMAIL_HOST': "smtp.gmail.com",
    #     'EMAIL_PORT': 587,
    #     'EMAIL_USE_TLS': True,
    #     'EMAIL_HOST_USER': "personal@gmail.com",
    #     'EMAIL_HOST_PASSWORD': "personal_password",
    #     'DEFAULT_FROM_EMAIL': "Personal <personal@gmail.com>",
    # },
}

# 默认使用的邮箱账户key
DEFAULT_EMAIL_ACCOUNT = 'default'

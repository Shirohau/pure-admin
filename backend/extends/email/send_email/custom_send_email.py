#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：custom_send_email.py
@Author  ：李小涛
@Date    ：2025/12/29 下午1:13 
@Explain : 邮件发送基类，支持多账户配置
"""
from typing import Optional

from django.core.mail import send_mail, get_connection

from application import settings


class CustomSendEmail:
    """邮件发送基类"""

    @staticmethod
    def get_email_config(account_key: Optional[str] = None) -> dict:
        """
        从settings获取邮件配置

        Args:
            account_key: 邮箱账户key，默认使用DEFAULT_EMAIL_ACCOUNT
        """
        email_accounts = getattr(settings, 'EMAIL_ACCOUNTS', {})
        if not email_accounts:
            raise Exception("未配置任何邮箱账户")

        if account_key is None:
            account_key = getattr(settings, 'DEFAULT_EMAIL_ACCOUNT', 'default')

        if account_key not in email_accounts:
            available = list(email_accounts.keys())
            raise Exception(f"邮箱账户 '{account_key}' 不存在。可用账户: {available}")

        cfg = email_accounts[account_key]
        email_config = {
            'host': cfg.get('EMAIL_HOST', ''),
            'port': cfg.get('EMAIL_PORT', 587),
            'use_tls': cfg.get('EMAIL_USE_TLS', True),
            'username': cfg.get('EMAIL_HOST_USER', ''),
            'password': cfg.get('EMAIL_HOST_PASSWORD', ''),
            'from_email': cfg.get('DEFAULT_FROM_EMAIL', ''),
        }

        missing = [k for k in ['host', 'username', 'password', 'from_email'] if not email_config[k]]
        if missing:
            raise Exception(f"邮箱账户 '{account_key}' 配置缺失以下项: {missing}")

        return email_config

    @staticmethod
    def get_available_accounts() -> list:
        """获取所有可用的邮箱账户列表"""
        return list(getattr(settings, 'EMAIL_ACCOUNTS', {}).keys())

    def send(self, email: str, subject: str, html_message: str,
             account_key: Optional[str] = None) -> dict:
        """
        发送邮件

        Args:
            email: 收件人邮箱地址
            subject: 邮件主题
            html_message: 邮件HTML内容
            account_key: 使用的邮箱账户key，默认使用默认账户

        Returns:
            {'success': bool, 'message': str}
        """
        if not getattr(settings, "ENABLE_EMAIL", False):
            return {"success": False, "message": "邮件功能未启用"}

        try:
            email_config = self.get_email_config(account_key)
            with get_connection(**email_config) as connection:
                send_mail(
                    subject=subject,
                    message='',
                    from_email=email_config["from_email"],
                    recipient_list=[email],
                    html_message=html_message,
                    connection=connection,
                )
            tag = f"(账户: {account_key})" if account_key else ""
            return {"success": True, "message": f"邮件发送成功{tag}"}
        except Exception as e:
            return {"success": False, "message": f"邮件发送失败: {e}"}

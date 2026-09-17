#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：email.py
@Author  ：李小涛
@Date    ：2026/05/28 
@Explain : 邮箱验证码服务
"""
from typing import Dict, Any
from django.contrib.auth import get_user_model
from extends.email.send_email.custom_send_email import CustomSendEmail
from .base import BaseVerification


class EmailProvider(BaseVerification):
    """邮箱验证码服务"""

    def _get_provider_type(self) -> str:
        """获取提供商类型标识"""
        return "email"

    def _validate_identifier(self, identifier: str) -> bool:
        """验证邮箱格式"""
        return identifier and '@' in identifier

    def _send_code_to_user(self, email: str, code: str, account_key: str = None, **kwargs) -> Dict[str, any]:
        """发送邮箱验证码到用户"""
        # 构建邮件内容
        subject = '邮箱验证码'
        html_message = f"""
        <p>您好，</p>
        <p>您的邮箱验证码是：<strong style="font-size: 24px; color: #007bff;">{code}</strong></p>
        <p>验证码有效期为 {self.expire_time // 60} 分钟，请勿泄露给他人。</p>
        <p>如果这不是您本人的操作，请忽略此邮件。</p>
        """
        
        try:
            # 发送邮件
            email_sender = CustomSendEmail()
            result = email_sender.send(email, subject, html_message, account_key=account_key)
            
            if result['success']:
                return {"success": True, "message": "验证码已发送至邮箱"}
            else:
                return {"success": False, "message": result['message']}
                
        except Exception as e:
            return {"success": False, "message": f"发送失败: {str(e)}"}

    def email_login(self, email: str, code: str, request) -> Dict[str, Any]:
        """
        处理邮箱验证码登录/注册
        :param email: 邮箱地址
        :param code: 验证码
        :param request: DRF Request对象
        :return: 登录响应结果
        """
        user = get_user_model()
        
        return self._handle_login_or_register(
            identifier=email,
            code=code,
            request=request,
            find_user_callback=lambda e: user.objects.filter(email=e).first(),
            create_user_callback=lambda e: self._create_email_user(e)
        )

    def _create_email_user(self, email: str):
        """创建邮箱用户"""
        user = get_user_model()
        
        # 使用邮箱前缀作为用户名（如果已存在，添加后缀）
        base_username = email.split('@')[0]
        username = self._generate_unique_username(base_username)
        
        # 创建用户
        user = user.objects.create(
            username=username,
            email=email,
            name=username
        )
        return user

    def reset_password(self, email: str, code: str, new_password: str) -> Dict[str, Any]:
        """
        处理密码重置
        :param email: 邮箱地址
        :param code: 验证码
        :param new_password: 新密码
        :return: 操作结果
        """
        user = get_user_model()
        
        return self._handle_password_reset(
            identifier=email,
            code=code,
            new_password=new_password,
            find_user_callback=lambda e: user.objects.filter(email=e).first()
        )

    def register(self, email: str, code: str, username: str = '', password: str = '', request = None) -> Dict[str, Any]:
        """
        通过邮箱验证码注册新用户
        :param email: 邮箱地址
        :param code: 验证码
        :param username: 用户名（可选，不传则使用邮箱前缀）
        :param password: 密码（可选）
        :param request: DRF Request对象
        :return: 注册响应结果
        """
        user = get_user_model()
        
        return self._handle_register(
            identifier=email,
            code=code,
            username=username,
            password=password,
            request=request,
            find_user_callback=lambda e: user.objects.filter(email=e).first(),
            create_user_callback=lambda uname, e: user.objects.create(
                username=uname,
                email=e,
                name=uname
            )
        )

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：change_password.py
@Author  ：李小涛
@Date    ：2025/12/29 上午8:40
@Explain : 密码重置通知邮件
"""
import os

from .custom_send_email import CustomSendEmail

admin_url = f"http://{os.environ.get('ADMIN_URL', '')}"


class ChangePassword(CustomSendEmail):
    """密码重置通知邮件"""

    def __init__(self, userinfo, subject: str = "数据系统账号密码"):
        self.userinfo = userinfo
        self.subject = subject

    def start(self):
        """发送密码重置邮件"""
        username = self.userinfo.get("username", "")
        user_email = self.userinfo.get("user_email", "")
        mobile = self.userinfo.get("mobile", "")
        password = self.userinfo.get("password", "")
        name = self.userinfo.get("name", "")
        html_message = f"""
        <p>{name}，您好。</p>
        <p>您的密码重置了，请使用新密码登录数据系统（<a href="{admin_url}">{admin_url}</a>），谢谢。</p>
        <p>账号：以下方式均可以登录</p>
            <ul>
             <li>账号：{username}</li>
             <li>工作邮箱：{user_email}</li>
             <li>手机号：{mobile}</li>
            </ul>
        <p>密码：{password}</p>

        <a href="{admin_url}" 
            style="
                display: inline-block; 
                padding: 10px 20px; 
                background-color: #007bff; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px;
            ">
            登录数据系统
        </a>              
        """
        return self.send(user_email, self.subject, html_message)

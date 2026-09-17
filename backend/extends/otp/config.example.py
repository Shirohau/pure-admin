#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：config.py
@Author  ：李小涛
@Date    ：2026/5/22
@Explain : 一次性密码配置

说明：
- 生产环境建议使用环境变量或专门的配置管理工具
- 不要将此文件提交到版本控制系统（如果包含敏感信息）
"""

# 短信登录配置
PHONE_CONFIG = {
    "access_key_id": "",  # AccessKey ID
    "access_key_secret": "",  # AccessKey Secret
    "sign_name": "",  # 短信签名
    "template_code": ""  # 短信模板代码
}

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：config.py
@Author  ：李小涛
@Date    ：2026/5/22
@Explain : OAuth2 第三方登录平台配置

说明：
- 所有平台的OAuth配置都放在这里
- 生产环境建议使用环境变量或专门的配置管理工具
- 不要将此文件提交到版本控制系统（如果包含敏感信息）
"""

from typing import Dict, Any

# 前端回调地址（统一配置）
OAUTH_REDIRECT_URI = "http://127.0.0.1:8080/callback"

# 微博 OAuth 配置
WEIBO_CONFIG: Dict[str, Dict[str, Any]] = {
    "PC": {
        "client_id": "",  # 应用Key
        "client_secret": "",  # 应用Secret
        "redirect_uri": OAUTH_REDIRECT_URI,  # 回调地址
        "authorize_uri": "https://api.weibo.com/oauth2/authorize",  # oauth2 认证地址
        "token_uri": "https://api.weibo.com/oauth2/access_token",  # 登录授权地址
        "userinfo_uri": "https://api.weibo.com/2/users/show.json",  # 用户查询地址
    },
    "M": {
        "client_id": "",
        "client_secret": "",
        "redirect_uri": OAUTH_REDIRECT_URI,  # 移动端可以使用不同的回调地址
        "authorize_uri": "https://api.weibo.com/oauth2/authorize",
        "token_uri": "https://api.weibo.com/oauth2/access_token",
        "userinfo_uri": "https://api.weibo.com/2/users/show.json",
    }
}

# Gitee 码云 OAuth 配置
GITEE_CONFIG: Dict[str, Dict[str, Any]] = {
    "PC": {
        "client_id": "",  # 应用Key
        "client_secret": "",  # 应用Secret
        "redirect_uri": OAUTH_REDIRECT_URI,  # 回调地址
        "authorize_uri": "https://gitee.com/oauth/authorize",  # oauth2 认证地址
        "token_uri": "https://gitee.com/oauth/token",  # 登录授权地址
        "userinfo_uri": "https://gitee.com/api/v5/user",  # 用户查询地址
    },
    "M": {
        "client_id": "",
        "client_secret": "",
        "redirect_uri": OAUTH_REDIRECT_URI,
        "authorize_uri": "https://gitee.com/oauth/authorize",
        "token_uri": "https://gitee.com/oauth/token",
        "userinfo_uri": "https://gitee.com/api/v5/user",
    }
}

# GitHub OAuth 配置
GITHUB_CONFIG: Dict[str, Dict[str, Any]] = {
    "PC": {
        "client_id": "",  # 应用Key
        "client_secret": "",  # 应用Secret
        "redirect_uri": OAUTH_REDIRECT_URI,  # 回调地址
        "authorize_uri": "https://github.com/login/oauth/authorize",  # oauth2 认证地址
        "token_uri": "https://github.com/login/oauth/access_token",  # 获取Access Token
        "userinfo_uri": "https://api.github.com/user",  # 用户查询地址
    },
    "M": {
        "client_id": "",
        "client_secret": "",
        "redirect_uri": OAUTH_REDIRECT_URI,
        "authorize_uri": "https://github.com/login/oauth/authorize",
        "token_uri": "https://github.com/login/oauth/access_token",
        "userinfo_uri": "https://api.github.com/user",
    }
}

# 企业微信 OAuth 配置
WECOM_CONFIG: Dict[str, Dict[str, Any]] = {
    "PC": {
        "corpid": "",  # 替换为企业ID
        "agentid": "",  # 替换为自建应用ID
        "corpsecret": "",  # 替换为自建应用Secret
        "redirect_uri": OAUTH_REDIRECT_URI,
        "authorize_uri": "https://open.work.weixin.qq.com/wwopen/sso/qrConnect",
        "token_uri": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
        "userinfo_uri": "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
    },
    "M": {
        "corpid": "",
        "agentid": "",
        "corpsecret": "",
        "redirect_uri": OAUTH_REDIRECT_URI,
        "authorize_uri": "https://open.work.weixin.qq.com/wwopen/sso/qrConnect",
        "token_uri": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
        "userinfo_uri": "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
    }
}

# qq OAuth 配置
QQ_CONFIG: Dict[str, Dict[str, Any]] = {
    "PC": {
        "client_id": "",  # 应用 ID
        "client_secret": "",  # 应用 Key
        "redirect_uri": OAUTH_REDIRECT_URI,  # 回调地址
        "authorize_uri": "https://graph.qq.com/oauth2.0/authorize",  # oauth2 认证地址
        "token_uri": "https://graph.qq.com/oauth2.0/token",  # 获取Access Token
        "userinfo_uri": "https://graph.qq.com/user/get_user_info",  # 用户查询地址
    },
    "M": {
        "client_id": "",
        "client_secret": "",
        "redirect_uri": OAUTH_REDIRECT_URI,
        "authorize_uri": "https://gitee.com/oauth/authorize",
        "token_uri": "https://gitee.com/oauth/token",
        "userinfo_uri": "https://gitee.com/api/v5/user",
    }
}

# 平台配置映射表
PLATFORM_CONFIGS = {
    "weibo": WEIBO_CONFIG,
    "github": GITHUB_CONFIG,
    "gitee": GITEE_CONFIG,
    "wecom": WECOM_CONFIG,
    "qq": QQ_CONFIG
}


def get_platform_config(platform: str, kind: str) -> Dict[str, Any]:
    """
    获取指定平台和类型的配置

    :param platform: 平台名称 (weibo/gitee/work_weixin)
    :param kind: 平台类型 (PC/M)
    :return: 配置字典
    :raises ValueError: 当平台或类型不支持时
    """
    if platform not in PLATFORM_CONFIGS:
        raise ValueError(f"不支持的OAuth平台: {platform}")

    platform_config = PLATFORM_CONFIGS[platform]

    if kind not in platform_config:
        raise ValueError(f"平台 {platform} 不支持的类型: {kind}")

    return platform_config[kind].copy()


def get_supported_platforms() -> list:
    """获取支持的平台列表"""
    return list(PLATFORM_CONFIGS.keys())

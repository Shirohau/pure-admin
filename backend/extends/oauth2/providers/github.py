#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：github.py
@Author  ：李小涛
@Date    ：2025/9/11 下午4:56 
@Explain : GitHub OAuth 实现 ： https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
"""
from typing import Dict, Any
from urllib.parse import parse_qs

from .base import OAuthProvider, OAuthError


class GithubProvider(OAuthProvider):
    """GitHub OAuth 2.0 实现"""

    platform_name = "github"

    def get_access_token(self) -> Dict[str, Any]:
        """
        通过授权码换取 access_token
        API: POST https://github.com/login/oauth/access_token
        GitHub 默认返回 URL-encoded 格式，设置 Accept: application/json 可返回 JSON
        """
        self._validate_config(['client_id', 'client_secret', 'redirect_uri'])

        url = self.config['token_uri']
        data = {
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'code': self.code,
            'redirect_uri': self.config['redirect_uri'],
        }
        headers = {'Accept': 'application/json'}
        return self._make_request(method='POST', url=url, data=data, headers=headers)

    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息
        API: GET https://api.github.com/user
        """
        # 获取 access_token
        token_resp = self.get_access_token()

        # GitHub 返回 JSON 时可直接取 access_token 字段；
        # 兼容 URL-encoded 回退场景（如未设置 Accept header 时）
        access_token = token_resp.get('access_token')
        if not access_token and 'text' in token_resp:
            params = parse_qs(token_resp['text'])
            access_token = params.get('access_token', [None])[0]

        if not access_token:
            raise OAuthError(
                "无法获取access_token",
                error_code="TOKEN_EXCHANGE_FAILED",
                platform=self.platform_name
            )

        url = self.config['userinfo_uri']
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Accept': 'application/json',
        }
        resp = self._make_request(method='GET', url=url, headers=headers)

        # GitHub 返回 login 作为用户名，name 为显示名称，id 为数字
        return {
            "uid": str(resp.get('id', '')),
            "uname": resp.get('login', resp.get('name', '')),
            "uinfo": resp
        }

    def get_authorize_url(self, state: str = None, scope: str = None) -> str:
        """
        生成GitHub授权URL
        :param state: CSRF状态码
        :param scope: 授权范围，如'user,repo'（多个用逗号分隔）
        :return: 授权URL
        """
        self._validate_config(['client_id', 'redirect_uri'])

        base_url = self.config['authorize_uri']
        params = [
            f"client_id={self.config['client_id']}",
            f"redirect_uri={self.config['redirect_uri']}",
            "response_type=code"
        ]

        if state:
            params.append(f"state={state}")
        if scope:
            params.append(f"scope={scope}")

        return f"{base_url}?{'&'.join(params)}"

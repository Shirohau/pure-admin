#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：weibo.py
@Author  ：李小涛
@Date    ：2025/9/11 下午3:58 
@Explain : 微博 OAuth 实现 ： https://open.weibo.com/wiki/Oauth2/authorize
"""
from typing import Dict, Any

from .base import OAuthProvider


class WeiboProvider(OAuthProvider):
    """微博 OAuth 2.0 实现"""

    platform_name = "weibo"

    def get_access_token(self) -> Dict[str, Any]:
        """
        通过授权码换取 access_token
        API: POST https://api.weibo.com/oauth2/access_token
        """
        self._validate_config(['client_id', 'client_secret', 'redirect_uri'])

        url = self.config['token_uri']
        data = {
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'grant_type': 'authorization_code',
            'code': self.code,
            'redirect_uri': self.config['redirect_uri'],
        }
        return self._make_request(method='POST', url=url, data=data)

    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息
        API: GET https://api.weibo.com/2/users/show.json
        """
        # 获取 access_token
        token_resp = self.get_access_token()
        access_token = token_resp.get('access_token')
        uid = token_resp.get('uid')

        if not access_token or not uid:
            from .base import OAuthError
            raise OAuthError(
                "无法获取access_token或uid",
                error_code="TOKEN_EXCHANGE_FAILED",
                platform=self.platform_name
            )

        url = self.config['userinfo_uri']
        params = {'access_token': access_token, 'uid': uid}
        resp = self._make_request(method='GET', url=url, params=params)

        return {
            "uid": str(resp.get('id', '')),
            "uname": resp.get('name', ''),
            "uinfo": resp
        }

    def get_authorize_url(self, state: str = None, scope: str = None) -> str:
        """
        生成微博授权URL
        :param state: CSRF状态码
        :param scope: 授权范围，如'email'
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

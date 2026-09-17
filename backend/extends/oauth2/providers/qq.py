#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：qq.py
@Author  ：李小涛
@Date    ：2026/8/2
@Explain : QQ OAuth 实现 ： https://wiki.connect.qq.com/使用authorization_code获取access_token
"""
import re
from typing import Dict, Any
from urllib.parse import parse_qs

from .base import OAuthProvider, OAuthError


class QQProvider(OAuthProvider):
    """QQ OAuth 2.0 实现"""

    platform_name = "qq"

    def get_access_token(self) -> Dict[str, Any]:
        """
        通过授权码换取 access_token
        API: GET https://graph.qq.com/oauth2.0/token
        注意：QQ 此接口返回 URL-encoded 文本（access_token=xxx&expires_in=xxx），非 JSON
        """
        self._validate_config(['client_id', 'client_secret', 'redirect_uri'])

        url = self.config['token_uri']
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'code': self.code,
            'redirect_uri': self.config['redirect_uri'],
        }
        resp = self._make_request(method='GET', url=url, params=params)

        # 解析 URL-encoded 文本响应
        if 'text' in resp:
            data = parse_qs(resp['text'])
            return {k: v[0] for k, v in data.items()}
        return resp

    def _get_openid(self, access_token: str) -> str:
        """
        获取 QQ 用户的 openid（唯一标识）
        API: GET https://graph.qq.com/oauth2.0/me
        响应为 JS 回调格式：callback( {"client_id":"...","openid":"..."} );
        """
        url = self.config.get('openid_uri')
        if not url:
            raise OAuthError(
                "缺少必要配置: openid_uri",
                error_code="MISSING_CONFIG",
                platform=self.platform_name
            )
        params = {'access_token': access_token}
        resp = self._make_request(method='GET', url=url, params=params)

        text = resp.get('text', '')
        # 正则提取 openid（兼容 callback(...) 包裹格式）
        match = re.search(r'"openid"\s*:\s*"([^"]+)"', text)
        if not match:
            raise OAuthError(
                "获取QQ openid 失败",
                error_code="TOKEN_EXCHANGE_FAILED",
                platform=self.platform_name
            )
        return match.group(1)

    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息
        API: GET https://graph.qq.com/user/get_user_info
        """
        # 获取 access_token
        token_resp = self.get_access_token()
        access_token = token_resp.get('access_token')

        if not access_token:
            raise OAuthError(
                "无法获取access_token",
                error_code="TOKEN_EXCHANGE_FAILED",
                platform=self.platform_name
            )

        # 获取 openid
        openid = self._get_openid(access_token)

        url = self.config['userinfo_uri']
        params = {
            'access_token': access_token,
            'oauth_consumer_key': self.config['client_id'],
            'openid': openid,
            'format': 'json',
        }
        user_resp = self._make_request(method='GET', url=url, params=params)

        # QQ 用户信息接口 ret != 0 表示失败
        if user_resp.get('ret') != 0:
            raise OAuthError(
                user_resp.get('msg', '获取QQ用户信息失败'),
                error_code="QQ_API_ERROR",
                platform=self.platform_name
            )

        return {
            "uid": openid,
            "uname": user_resp.get('nickname', openid),
            "uinfo": user_resp
        }

    def get_authorize_url(self, state: str = None, scope: str = None) -> str:
        """
        生成QQ授权URL
        :param state: CSRF状态码
        :param scope: 授权范围，默认 get_user_info
        :return: 授权URL
        """
        self._validate_config(['client_id', 'redirect_uri'])

        base_url = self.config['authorize_uri']
        params = [
            f"client_id={self.config['client_id']}",
            f"redirect_uri={self.config['redirect_uri']}",
            "response_type=code",
            f"scope={scope or 'get_user_info'}",
        ]

        if state:
            params.append(f"state={state}")

        return f"{base_url}?{'&'.join(params)}"

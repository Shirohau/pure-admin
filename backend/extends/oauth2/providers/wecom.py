#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：wecom.py
@Author  ：李小涛
@Date    ：2025/9/11 下午4:00 
@Explain : 企业微信 OAuth 实现 ： https://developer.work.weixin.qq.com/document/path/91022
"""
from typing import Dict, Any

from .base import OAuthProvider


class WecomProvider(OAuthProvider):
    """企业微信 OAuth 2.0 实现"""

    platform_name = "wecom"

    def get_access_token(self) -> Dict[str, Any]:
        """
        获取企业微信 access_token
        API: GET https://qyapi.weixin.qq.com/cgi-bin/gettoken
        """
        self._validate_config(['appid', 'corpsecret'])

        url = self.config['token_uri']
        params = {
            'corpid': self.config['appid'],
            'corpsecret': self.config['corpsecret'],
        }
        return self._make_request(method='GET', url=url, params=params)

    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息
        API: GET https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo
        :return: 标准化的用户信息
        """
        # 获取 access_token
        token_resp = self.get_access_token()
        access_token = token_resp.get('access_token')

        if not access_token:
            from .base import OAuthError
            raise OAuthError(
                "无法获取access_token",
                error_code="TOKEN_EXCHANGE_FAILED",
                platform=self.platform_name
            )

        # 通过 code 获取用户信息
        url = self.config['userinfo_uri']
        params = {
            'access_token': access_token,
            'code': self.code,
        }
        user_resp = self._make_request(method='GET', url=url, params=params)
        # 返回标准化格式
        return {
            "uid": user_resp.get('userid', ''),
            "uname": user_resp.get('userid', ''),
            "uinfo": user_resp
        }

    def get_authorize_url(self, state: str = None, scope: str = None) -> str:
        """
        生成企业微信扫码登录URL
        :param state: CSRF状态码（企业微信称为state）
        :param scope: 授权范围（企业微信固定为snsapi_login）
        :return: 授权URL
        """
        self._validate_config(['corpid', 'agentid', 'redirect_uri'])

        base_url = self.config['authorize_uri']
        params = [
            f"appid={self.config['corpid']}",
            f"agentid={self.config['agentid']}",
            f"redirect_uri={self.config['redirect_uri']}",
            "response_type=code",
            "scope=snsapi_login",
        ]

        if state:
            params.append(f"state={state}#wechat_redirect")
        else:
            params.append("state=STATE#wechat_redirect")

        return f"{base_url}?{'&'.join(params)}"

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：wechat.py
@Author  ：李小涛
@Date    ：2026/8/2
@Explain : 微信 OAuth 实现（公众号网页授权 + 小程序登录）
           - PC（公众号网页授权）：https://developers.weixin.qq.com/doc/offiaccount/OA_Web_Apps/Wechat_webpage_authorization.html
           - M（小程序登录）：https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-login/code2Session.html
"""
from typing import Dict, Any

from .base import OAuthProvider, OAuthError


class WechatProvider(OAuthProvider):
    """微信 OAuth 2.0 实现（H5 网页授权与小程序 code2session 双模式）"""

    platform_name = "wechat"

    def get_access_token(self) -> Dict[str, Any]:
        """
        通过授权码换取登录态（按 token_uri 自动区分两种模式）：
        - 网页授权（sns/oauth2/access_token）：返回 access_token + openid
        - 小程序（sns/jscode2session）：返回 openid + session_key（无 access_token）
        """
        self._validate_config(['appid', 'secret'])

        url = self.config['token_uri']
        params = {
            'appid': self.config['appid'],
            'secret': self.config['secret'],
            'grant_type': 'authorization_code',
        }
        # 小程序 code 参数名为 js_code，网页授权为 code
        if url.endswith('jscode2session'):
            params['js_code'] = self.code
        else:
            params['code'] = self.code

        resp = self._make_request(method='GET', url=url, params=params)

        # 微信接口错误统一返回 {"errcode": 400xx, "errmsg": "..."}
        if resp.get('errcode'):
            raise OAuthError(
                resp.get('errmsg', '微信接口调用失败'),
                error_code="WECHAT_API_ERROR",
                platform=self.platform_name
            )
        return resp

    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息：
        - 网页授权：access_token + openid 调 sns/userinfo 获取昵称头像
        - 小程序：jscode2session 仅返回 openid/session_key，无用户资料，
          以 openid 作为用户名（如需昵称头像需前端 wx.getUserProfile，本项目不涉及）
        """
        token_resp = self.get_access_token()
        openid = token_resp.get('openid', '')

        if not openid:
            raise OAuthError(
                "无法获取微信 openid",
                error_code="TOKEN_EXCHANGE_FAILED",
                platform=self.platform_name
            )

        access_token = token_resp.get('access_token')
        userinfo_uri = self.config.get('userinfo_uri', '')

        # 小程序模式：无 access_token 与用户资料接口，直接返回 openid
        if not access_token or not userinfo_uri:
            return {
                "uid": openid,
                "uname": openid,
                "uinfo": token_resp
            }

        # 网页授权模式：拉取用户昵称与头像
        url = userinfo_uri
        params = {
            'access_token': access_token,
            'openid': openid,
            'lang': 'zh_CN',
        }
        user_resp = self._make_request(method='GET', url=url, params=params)

        if user_resp.get('errcode'):
            raise OAuthError(
                user_resp.get('errmsg', '获取微信用户信息失败'),
                error_code="WECHAT_API_ERROR",
                platform=self.platform_name
            )

        return {
            "uid": openid,
            "uname": user_resp.get('nickname', openid),
            "uinfo": user_resp
        }

    def get_authorize_url(self, state: str = None, scope: str = None) -> str:
        """
        生成微信网页授权 URL（仅 PC 模式使用；小程序由 uni.login 直接获取 code）
        :param state: CSRF状态码（微信要求 state 必须以 #wechat_redirect 结尾）
        :param scope: 授权范围，默认 snsapi_userinfo
        :return: 授权URL
        """
        self._validate_config(['appid', 'redirect_uri'])

        base_url = self.config['authorize_uri']
        params = [
            f"appid={self.config['appid']}",
            f"redirect_uri={self.config['redirect_uri']}",
            "response_type=code",
            f"scope={scope or 'snsapi_userinfo'}",
        ]

        if state:
            params.append(f"state={state}#wechat_redirect")
        else:
            params.append("state=STATE#wechat_redirect")

        return f"{base_url}?{'&'.join(params)}"

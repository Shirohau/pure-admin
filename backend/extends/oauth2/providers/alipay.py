#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：alipay.py
@Author  ：李小涛
@Date    ：2026/8/2
@Explain : 支付宝 OAuth 实现 ： https://opendocs.alipay.com/open/284/106370
           授权登录流程（第三方应用）：
           1. 跳转授权页 publicAppAuthorize（scope=auth_base 仅拿 user_id，auth_user 可拿昵称头像）
           2. 授权码换 token：alipay.system.oauth.token（RSA2 签名）
           3. 可选拉取用户资料：alipay.user.info.share（需 auth_user scope + auth_token）
"""
import base64
import time
from typing import Dict, Any

from .base import OAuthProvider, OAuthError

# 支付宝网关成功状态码
ALIPAY_SUCCESS_CODE = "10000"


class AlipayProvider(OAuthProvider):
    """支付宝 OAuth 2.0 实现（RSA2 签名）"""

    platform_name = "alipay"

    def _sign(self, params: Dict[str, Any]) -> str:
        """
        支付宝 RSA2 签名（SHA256withRSA）：
        将除 sign 外的参数按 key 字典序排序，拼接为 k1=v1&k2=v2 后私钥签名，base64 编码。
        :param params: 待签名参数字典（已包含除 sign 外的全部参数）
        :return: base64 签名串
        """
        try:
            from Crypto.PublicKey import RSA
            from Crypto.Signature import pkcs1_15
            from Crypto.Hash import SHA256
        except ImportError:
            raise OAuthError(
                "缺少 pycryptodome 依赖，请执行 pip install pycryptodome",
                error_code="MISSING_DEPENDENCY",
                platform=self.platform_name
            )

        private_key = self.config.get('private_key', '')
        if not private_key or private_key.startswith('your_'):
            raise OAuthError(
                "缺少支付宝应用私钥配置（private_key）",
                error_code="MISSING_CONFIG",
                platform=self.platform_name
            )

        # 字典序排序并拼接待签名内容（不包含 sign 本身）
        content = '&'.join(f"{k}={params[k]}" for k in sorted(params))
        try:
            key = RSA.import_key(private_key)
            digest = SHA256.new(content.encode('utf-8'))
            signature = pkcs1_15.new(key).sign(digest)
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            raise OAuthError(
                f"支付宝签名失败: {str(e)}",
                error_code="SIGN_ERROR",
                platform=self.platform_name
            )

    def _gateway_request(self, method: str, biz_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        支付宝开放平台网关统一请求（公共参数 + RSA2 签名 + 表单提交）
        :param method: 接口方法名（alipay.system.oauth.token / alipay.user.info.share）
        :param biz_params: 业务参数（code / grant_type / auth_token 等）
        :return: 网关响应 JSON
        """
        self._validate_config(['app_id', 'private_key'])

        params = {
            'app_id': self.config['app_id'],
            'method': method,
            'format': 'JSON',
            'charset': 'utf-8',
            'sign_type': 'RSA2',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0',
            **biz_params,
        }
        params['sign'] = self._sign(params)

        url = self.config['token_uri']
        return self._make_request(method='POST', url=url, data=params)

    def get_access_token(self) -> Dict[str, Any]:
        """
        通过授权码换取 access_token
        API: alipay.system.oauth.token
        成功响应：{"alipay_system_oauth_token_response": {"code":"10000","user_id":"...","access_token":"..."}}
        """
        resp = self._gateway_request('alipay.system.oauth.token', {
            'grant_type': 'authorization_code',
            'code': self.code,
        })

        # 解析业务响应（失败时返回 error_response）
        data = resp.get('alipay_system_oauth_token_response') or {}
        if data.get('code') != ALIPAY_SUCCESS_CODE or not data.get('user_id'):
            error_info = resp.get('error_response') or data
            raise OAuthError(
                error_info.get('sub_msg', error_info.get('msg', '支付宝授权失败')),
                error_code="ALIPAY_API_ERROR",
                platform=self.platform_name
            )
        return data

    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息：
        - auth_base 授权：仅能获取 user_id（支付宝不开放未授权的用户资料），uname 使用 user_id
        - auth_user 授权：额外调用 alipay.user.info.share 拉取昵称/头像（失败不影响登录）
        """
        token_resp = self.get_access_token()
        user_id = token_resp.get('user_id', '')
        access_token = token_resp.get('access_token', '')

        if not user_id:
            raise OAuthError(
                "无法获取支付宝 user_id",
                error_code="TOKEN_EXCHANGE_FAILED",
                platform=self.platform_name
            )

        # 仅 auth_user scope 且配置了 userinfo_uri 时尝试拉取昵称头像
        uname = user_id
        userinfo_uri = self.config.get('userinfo_uri', '')
        if access_token and userinfo_uri:
            try:
                info_resp = self._gateway_request('alipay.user.info.share', {
                    'auth_token': access_token,
                })
                info_data = info_resp.get('alipay_user_info_share_response') or {}
                if info_data.get('code') == ALIPAY_SUCCESS_CODE:
                    nick_name = info_data.get('nick_name', '')
                    if nick_name:
                        uname = nick_name
                    # 合并原始用户资料，便于 uinfo 完整落库
                    token_resp['user_info'] = info_data
            except OAuthError:
                # auth_base 授权下拉取资料必然失败，属预期行为，忽略即可
                pass

        return {
            "uid": user_id,
            "uname": uname,
            "uinfo": token_resp
        }

    def get_authorize_url(self, state: str = None, scope: str = None) -> str:
        """
        生成支付宝授权URL
        :param state: CSRF状态码
        :param scope: 授权范围，默认 auth_base（auth_user 可获取昵称头像）
        :return: 授权URL
        """
        self._validate_config(['app_id', 'redirect_uri'])

        base_url = self.config['authorize_uri']
        params = [
            f"app_id={self.config['app_id']}",
            f"redirect_uri={self.config['redirect_uri']}",
            f"scope={scope or self.config.get('scope', 'auth_base')}",
        ]

        if state:
            params.append(f"state={state}")

        return f"{base_url}?{'&'.join(params)}"

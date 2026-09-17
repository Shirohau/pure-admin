# oauth/base.py
"""
OAuth 平台抽象基类
所有具体平台实现必须继承此类
提供统一的HTTP请求、错误处理、日志记录等功能
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

import requests
from requests.exceptions import RequestException


class OAuthError(Exception):
    """OAuth相关异常基类"""

    def __init__(self, message: str, error_code: str = "OAUTH_ERROR", platform: str = None):
        self.message = message
        self.error_code = error_code
        self.platform = platform
        super().__init__(self.message)


class OAuthProvider(ABC):
    """第三方 OAuth 平台统一接口"""

    # 平台标识，子类应覆盖
    platform_name: str = "unknown"

    # 默认配置项，子类可覆盖
    default_config: Dict[str, Any] = {}

    def __init__(self, code: str = None, config: Dict[str, Any] = None):
        """
        初始化 Provider 上下文
        :param code: 授权码
        :param config: 平台配置字典（client_id, client_secret, redirect_uri 等）
        """
        self.code = code
        self.config = config or {}
        # 合并默认配置
        self._merge_default_config()

    def _merge_default_config(self):
        """合并默认配置，确保必要的配置项存在"""
        for key, value in self.default_config.items():
            if key not in self.config:
                self.config[key] = value

    def _validate_config(self, required_keys: list):
        """验证必要配置项是否存在"""
        missing_keys = [key for key in required_keys if key not in self.config]
        if missing_keys:
            raise OAuthError(
                f"缺少必要配置: {', '.join(missing_keys)}",
                error_code="MISSING_CONFIG",
                platform=self.platform_name
            )

    def _make_request(
            self,
            method: str = "GET",
            url: str = None,
            params: Dict[str, Any] = None,
            data: Dict[str, Any] = None,
            headers: Dict[str, str] = None,
            timeout: int = 30
    ) -> Dict[str, Any]:
        """
        统一的HTTP请求方法，包含错误处理和日志记录
        :param method: HTTP方法 (GET/POST)
        :param url: 请求URL
        :param params: URL参数
        :param data: 请求体数据
        :param headers: 请求头
        :param timeout: 超时时间（秒）
        :return: JSON响应数据
        """
        try:

            response = requests.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()

            # 尝试解析JSON响应
            try:
                result = response.json()
            except ValueError:
                result = {"text": response.text}

            return result

        except RequestException as e:
            error_msg = f"HTTP请求失败: {str(e)}"
            raise OAuthError(
                error_msg,
                error_code="HTTP_REQUEST_FAILED",
                platform=self.platform_name
            )
        except Exception as e:
            error_msg = f"请求异常: {str(e)}"
            raise OAuthError(
                error_msg,
                error_code="REQUEST_EXCEPTION",
                platform=self.platform_name
            )

    @abstractmethod
    def get_access_token(self) -> Dict[str, Any]:
        """
        通过授权码换取 access_token
        :return: 包含access_token的响应数据
        """
        raise NotImplementedError("子类必须实现 get_access_token")

    @abstractmethod
    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息
        :return: 标准化的用户信息字典，包含 uid, uname, uinfo
        """
        raise NotImplementedError("子类必须实现 get_user_info")

    def get_authorize_url(self, state: str = None, scope: str = None) -> str:
        """
        生成授权URL（可选实现）
        :param state: CSRF保护状态码
        :param scope: 授权范围
        :return: 授权URL
        """
        raise NotImplementedError("该平台不支持直接生成授权URL")

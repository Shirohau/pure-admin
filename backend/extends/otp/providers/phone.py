# -*- coding: utf-8 -*-
"""
短信验证码服务

"""
from typing import Dict, Any
from django.contrib.auth import get_user_model
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models

from .base import BaseVerification
from ..config import PHONE_CONFIG


class AlibabaCloud:
    """
    阿里云短信服务（单例模式）
    https://api.aliyun.com/api-tools/sdk/Dysmsapi?version=2017-05-25&language=python-tea&tab=primer-doc
    """
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.access_key_id = PHONE_CONFIG["access_key_id"]
            self.access_key_secret = PHONE_CONFIG["access_key_secret"]
            self.sign_name = PHONE_CONFIG["sign_name"]
            self.template_code = PHONE_CONFIG["template_code"]
            self.initialized = True

    def create_client(self) -> Dysmsapi20170525Client:
        """
        使用凭据初始化阿里云短信客户端
        @return: Client
        @throws Exception
        """
        if self._client is None:
            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret
            )
            config.endpoint = f'dysmsapi.aliyuncs.com'
            self._client = Dysmsapi20170525Client(config)
        return self._client


class PhoneProvider(BaseVerification):
    """短信验证码服务"""

    def _get_provider_type(self) -> str:
        """获取提供商类型标识"""
        return "phone"

    def _validate_identifier(self, identifier: str) -> bool:
        """验证手机号格式"""
        return identifier and identifier.isdigit() and len(identifier) == 11

    def _send_code_to_user(self, phone_number: str, code: str, **kwargs) -> Dict[str, any]:
        """发送短信验证码到用户"""
        client = AlibabaCloud().create_client()
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            phone_numbers=phone_number,
            sign_name=AlibabaCloud().sign_name,
            template_code=AlibabaCloud().template_code,
            template_param=f'{{"code":"{code}"}}'
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = client.send_sms_with_options(send_sms_request, runtime)

            if resp.body.code == 'OK':
                return {"success": True, "message": "短信发送成功"}
            else:
                return {
                    "success": False,
                    "message": f"短信发送失败: {resp.body.message}"
                }
        except Exception as error:
            return {
                "success": False,
                "message": f"短信发送异常: {str(error)}"
            }

    def sms_login(self, phone: str, code: str, request) -> Dict[str, Any]:
        """
        处理短信验证码登录/注册
        :param phone: 手机号
        :param code: 验证码
        :param request: DRF Request对象
        :return: 登录响应结果
        """
        user = get_user_model()

        return self._handle_login_or_register(
            identifier=phone,
            code=code,
            request=request,
            find_user_callback=lambda p: user.objects.filter(mobile=p).first(),
            create_user_callback=lambda p: self._create_phone_user(p)
        )

    def _create_phone_user(self, phone: str):
        """创建手机号用户"""
        user = get_user_model()

        # 使用手机号作为用户名（如果手机号已存在，添加后缀）
        username = self._generate_unique_username(phone)

        # 创建用户
        user = user.objects.create(
            username=username,
            mobile=phone,
            name=username
        )
        return user

    def reset_password(self, phone: str, code: str, new_password: str) -> Dict[str, Any]:
        """
        处理密码重置
        :param phone: 手机号
        :param code: 验证码
        :param new_password: 新密码
        :return: 操作结果
        """
        user = get_user_model()

        return self._handle_password_reset(
            identifier=phone,
            code=code,
            new_password=new_password,
            find_user_callback=lambda p: user.objects.filter(mobile=p).first()
        )

    def register(self, username: str, phone: str, code: str, password: str, request) -> Dict[str, Any]:
        """
        通过手机号验证码注册新用户
        :param username: 用户名
        :param phone: 手机号
        :param code: 验证码
        :param password: 密码
        :param request: DRF Request对象
        :return: 注册响应结果
        """
        user = get_user_model()

        return self._handle_register(
            identifier=phone,
            code=code,
            username=username,
            password=password,
            request=request,
            find_user_callback=lambda p: user.objects.filter(mobile=p).first(),
            create_user_callback=lambda uname, p: user.objects.create(
                username=uname,
                mobile=p,
                name=uname
            )
        )

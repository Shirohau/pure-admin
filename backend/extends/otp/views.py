#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：views.py
@Author  ：李小涛
@Date    ：2026/6/3 
@Explain : 验证码登录视图层
"""

from rest_framework import viewsets, serializers
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import error_response, success_response
from .providers.phone import PhoneProvider
from .providers.email import EmailProvider



class EmptySerializer(serializers.Serializer):
    """空序列化器，用于 DRF Spectacular 文档生成"""
    pass


@extend_schema(tags=["验证码服务"])
class OTPView(viewsets.ViewSet):
    """验证码登录管理视图（手机号/邮箱）"""
    serializer_class = EmptySerializer  # 用于 DRF Spectacular 文档生成

    @staticmethod
    def _get_provider(verify_type: str):
        """根据类型获取对应的 Provider"""
        if verify_type == 'phone':
            return PhoneProvider()
        elif verify_type == 'email':
            return EmailProvider()
        else:
            raise ValueError(f"不支持的验证类型: {verify_type}，仅支持 phone 或 email")

    @staticmethod
    def _validate_identifier(identifier: str, verify_type: str) -> bool:
        """验证标识符格式"""
        if verify_type == 'phone':
            return identifier and identifier.isdigit() and len(identifier) == 11
        elif verify_type == 'email':
            return identifier and '@' in identifier
        return False

    def _parse_request_params(self, request, required_fields: list, optional_fields: list = None):
        """
        通用请求参数解析和验证
        :param request: DRF Request对象
        :param required_fields: 必需字段列表，如 ['type', 'phone', 'code']
        :param optional_fields: 可选字段列表，如 ['account_key', 'password']
        :return: (verify_type, provider, params_dict) 或 error_response
        """
        if optional_fields is None:
            optional_fields = []

        # 获取 type 参数
        verify_type = request.data.get('type')
        if not verify_type:
            return error_response(message="缺少必要参数：type (phone/email)")

        # 获取 provider
        try:
            provider = self._get_provider(verify_type)
        except ValueError as e:
            return error_response(message=str(e))

        # 确定标识符字段名
        identifier_field = 'phone' if verify_type == 'phone' else 'email'

        # 构建参数字典
        params = {
            'verify_type': verify_type,
            'provider': provider,
            'identifier_field': identifier_field,
            'identifier': request.data.get(identifier_field),
        }

        # 添加其他必需字段
        for field in required_fields:
            if field == 'type' or field == identifier_field:
                continue  # 已处理
            value = request.data.get(field) or request.data.get(f'verify{field.capitalize()}', '')
            params[field] = value

        # 添加可选字段
        for field in optional_fields:
            params[field] = request.data.get(field)

        return params

    @extend_schema(summary="发送验证码", parameters=[])
    @action(methods=["POST"], detail=False, permission_classes=[], url_path='send-code')
    def send_code(self, request, *args, **kwargs):
        """
        发送验证码（支持短信和邮箱）
        
        请求体需包含：
        - type: 验证类型 (phone/email)
        - phone: 手机号码（type=phone 时必需，11位数字）
        - email: 邮箱地址（type=email 时必需）
        - account_key: 可选，使用的邮箱账户key（仅 email 类型）
        """
        params = self._parse_request_params(request, required_fields=['type'], optional_fields=['account_key'])
        if isinstance(params, Response):  # 参数解析失败时返回错误响应，直接返回
            return params
        verify_type = params['verify_type']
        provider = params['provider']
        identifier = params['identifier']

        # 验证标识符
        if not identifier:
            return error_response(message=f"缺少必要参数：{params['identifier_field']}")

        if not self._validate_identifier(identifier, verify_type):
            return error_response(message=f"{'手机号' if verify_type == 'phone' else '邮箱'}格式不正确")

        try:
            # 邮箱类型支持 account_key 参数
            send_kwargs = {}
            if verify_type == 'email' and params.get('account_key'):
                send_kwargs['account_key'] = params['account_key']

            result = provider.send_code(identifier, **send_kwargs)

            if result['success']:
                return success_response(message=result['message'])
            else:
                return error_response(message=result['message'])
        except Exception as e:
            return error_response(message=f"验证码发送失败: {str(e)}")

    @extend_schema(summary="验证码登录", parameters=[])
    @action(methods=["POST"], detail=False, permission_classes=[], url_path='login')
    def verification_login(self, request, *args, **kwargs):
        """
        验证码登录/注册（支持短信和邮箱）
        
        请求体需包含：
        - type: 验证类型 (phone/email)
        - phone: 手机号码（type=phone 时必需）
        - email: 邮箱地址（type=email 时必需）
        - code: 验证码
        """
        params = self._parse_request_params(request, required_fields=['type', 'code'])
        if isinstance(params, Response):
            return params

        verify_type = params['verify_type']
        provider = params['provider']
        identifier = params['identifier']
        code = params['code']

        # 验证参数
        if not all([identifier, code]):
            return error_response(message=f"缺少必要参数：{params['identifier_field']}, code")

        if not self._validate_identifier(identifier, verify_type):
            return error_response(message=f"{'手机号' if verify_type == 'phone' else '邮箱'}格式不正确")

        try:
            # 调用对应的登录方法
            if verify_type == 'phone':
                result = provider.sms_login(identifier, code, request)
            else:
                result = provider.email_login(identifier, code, request)

            if result['success']:
                return success_response(message=result['message'], data=result.get('data'))
            else:
                return error_response(message=result['message'])
        except Exception as e:
            return error_response(message=f"验证失败: {str(e)}")

    @extend_schema(summary="验证码重置密码", parameters=[])
    @action(methods=["POST"], detail=False, permission_classes=[], url_path='reset-password')
    def reset_password(self, request, *args, **kwargs):
        """
        忘记密码 - 通过验证码重置密码，无需登录（支持短信和邮箱）
        
        请求体需包含：
        - type: 验证类型 (phone/email)
        - phone: 手机号码（type=phone 时必需）
        - email: 邮箱地址（type=email 时必需）
        - code: 验证码
        - password: 新密码
        """
        params = self._parse_request_params(request, required_fields=['type', 'code', 'password'])
        if isinstance(params, Response):
            return params

        verify_type = params['verify_type']
        provider = params['provider']
        identifier = params['identifier']
        code = params['code']
        password = params['password']

        # 验证参数
        if not all([identifier, code, password]):
            return error_response(message=f"缺少必要参数：{params['identifier_field']}, code, password")

        if not self._validate_identifier(identifier, verify_type):
            return error_response(message=f"{'手机号' if verify_type == 'phone' else '邮箱'}格式不正确")

        if not password or len(password) < 6:
            return error_response(message="密码长度不能少于6位")

        try:
            result = provider.reset_password(identifier, code, password)

            if result['success']:
                return success_response(message=result['message'])
            else:
                return error_response(message=result['message'])
        except Exception as e:
            return error_response(message=f"密码重置失败: {str(e)}")

    @extend_schema(summary="验证码注册", parameters=[])
    @action(methods=["POST"], detail=False, permission_classes=[], url_path='register')
    def register(self, request, *args, **kwargs):
        """
        通过验证码注册新用户（支持短信和邮箱）

        请求体需包含：
        - type: 验证类型 (phone/email)
        - username: 用户名
        - phone: 手机号码（type=phone 时必需，11位数字）
        - email: 邮箱地址（type=email 时必需）
        - code: 验证码
        - password: 密码（可选，不传则自动生成）
        """
        params = self._parse_request_params(
            request,
            required_fields=['type', 'username', 'code'],
            optional_fields=['password']
        )
        if isinstance(params, Response):
            return params

        verify_type = params['verify_type']
        provider = params['provider']
        identifier = params['identifier']
        username = params['username']
        code = params['code']
        password = params.get('password', '')

        # 验证参数
        if not all([username, identifier, code]):
            return error_response(message=f"缺少必要参数：username, {params['identifier_field']}, code")

        if not self._validate_identifier(identifier, verify_type):
            return error_response(message=f"{'手机号' if verify_type == 'phone' else '邮箱'}格式不正确")

        if password and len(password) < 6:
            return error_response(message="密码长度不能少于6位")

        try:
            # 调用对应的注册方法
            if verify_type == 'phone':
                result = provider.register(username, identifier, code, password, request)
            else:
                result = provider.register(identifier, code, username, password, request)

            if result['success']:
                return success_response(message=result['message'], data=result.get('data'))
            else:
                return error_response(message=result['message'])
        except Exception as e:
            return error_response(message=f"注册失败: {str(e)}")

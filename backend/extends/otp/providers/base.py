#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：base.py
@Author  ：AI Assistant
@Date    ：2026/05/29 
@Explain : 验证码服务统一基类
"""
import random
from abc import ABC, abstractmethod

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.conf import settings
User = get_user_model()


class BaseVerification(ABC):
    """验证码服务统一基类"""

    # 默认配置
    DEFAULT_EXPIRE_TIME = 300  # 验证码过期时间（秒），5分钟
    DEFAULT_CODE_LENGTH = 6  # 验证码长度
    DEFAULT_RATE_LIMIT = 60  # 发送频率限制（秒）

    # 缓存键前缀
    CODE_CACHE_PREFIX = "verification_code"
    RATE_CACHE_PREFIX = "verification_rate"

    def __init__(self, expire_time: int = None, code_length: int = None, rate_limit: int = None):
        """
        初始化验证码服务
        :param expire_time: 验证码过期时间（秒）
        :param code_length: 验证码长度
        :param rate_limit: 发送频率限制（秒）
        """
        self.expire_time = expire_time or self.DEFAULT_EXPIRE_TIME
        self.code_length = code_length or self.DEFAULT_CODE_LENGTH
        self.rate_limit = rate_limit or self.DEFAULT_RATE_LIMIT

    def _generate_code(self) -> str:
        """生成指定位数的随机验证码"""
        min_value = 10 ** (self.code_length - 1)
        max_value = (10 ** self.code_length) - 1
        return str(random.randint(min_value, max_value))

    def _get_code_cache_key(self, identifier: str) -> str:
        """获取验证码缓存键"""
        return f"{self.CODE_CACHE_PREFIX}_{self._get_provider_type()}_{identifier}"

    def _get_rate_cache_key(self, identifier: str) -> str:
        """获取频率限制缓存键"""
        return f"{self.RATE_CACHE_PREFIX}_{self._get_provider_type()}_{identifier}"

    @abstractmethod
    def _get_provider_type(self) -> str:
        """获取提供商类型标识（用于缓存键区分）"""
        raise NotImplementedError("子类必须实现此方法")

    @abstractmethod
    def _validate_identifier(self, identifier):
        """验证标识符格式（手机号/邮箱）"""
        raise NotImplementedError("子类必须实现此方法")

    @abstractmethod
    def _send_code_to_user(self, identifier, code, **kwargs):
        """发送验证码到用户（具体实现由子类完成）"""
        raise NotImplementedError("子类必须实现此方法")

    def send_code(self, identifier, **kwargs):
        """
        发送验证码的通用流程
        :param identifier: 标识符（手机号/邮箱）
        :param kwargs: 其他参数
        :return: 包含success和message的字典
        """
        # 1. 验证标识符格式
        if not self._validate_identifier(identifier):
            return {"success": False, "message": f"{self._get_provider_type()}格式不正确"}

        # 2. 检查发送频率
        rate_key = self._get_rate_cache_key(identifier)
        if cache.get(rate_key):
            # 由于Django缓存API不直接支持获取TTL，我们返回一个固定的提示信息
            return {
                "success": False,
                "message": f"发送过于频繁，请稍后再试"
            }

        # 3. 生成验证码
        code = self._generate_code()

        # 4. 发送验证码
        result = self._send_code_to_user(identifier, code, **kwargs)

        # 5. 如果发送成功，存储验证码和设置频率限制
        if result['success']:
            code_key = self._get_code_cache_key(identifier)
            cache.set(code_key, code, timeout=self.expire_time)
            cache.set(rate_key, True, timeout=self.rate_limit)
        return result

    @staticmethod
    def verify_code(identifier: str, code: str, provider_type: str) -> bool:
        """
        验证验证码的通用方法
        :param identifier: 标识符（手机号/邮箱）
        :param code: 验证码
        :param provider_type: 提供商类型
        :return: 是否验证成功
        """
        if not identifier or not code:
            return False

        cache_key = f"verification_code_{provider_type}_{identifier}"
        cached_code = cache.get(cache_key)

        if cached_code and str(cached_code) == str(code):
            # 验证成功后删除验证码，防止重复使用
            cache.delete(cache_key)
            return True

        return False

    @staticmethod
    def _generate_unique_username(base_username: str) -> str:
        """
        生成唯一用户名
        :param base_username: 基础用户名
        :return: 唯一的用户名
        """
        # 检查用户名是否已存在
        if not User.objects.filter(username=base_username).exists():
            return base_username

        # 如果已存在，尝试 username_1, username_2... 直到找到唯一的
        for i in range(1, 100):
            username = f"{base_username}_{i}"
            if not User.objects.filter(username=username).exists():
                return username

        # 极端情况：添加随机后缀
        return f"{base_username}_{random.randint(1000, 9999)}"

    def _handle_login_or_register(self, identifier, code, request, find_user_callback, create_user_callback):
        """
        处理登录或注册的通用逻辑
        :param identifier: 标识符
        :param code: 验证码
        :param request: DRF Request对象
        :param find_user_callback: 查找用户的回调函数
        :param create_user_callback: 创建用户的回调函数
        :return: 登录/注册响应结果
        """
        # 1. 验证验证码
        provider_type = self._get_provider_type()
        is_valid = self.verify_code(identifier, code, provider_type)
        if not is_valid:
            return {"success": False, "message": "验证码错误或已过期"}

        # 2. 查找用户
        user = find_user_callback(identifier)

        if user:
            # 3. 用户存在，直接登录
            from extends.jwt.views import user_login
            data = user_login(user, request)
            return {"success": True, "message": "登录成功", "data": data}
        else:
            # 4. 用户不存在，检查是否允许自动注册
            if not getattr(settings, 'AUTO_REGISTER', False):
                return {"success": False, "message": f"该{provider_type}尚未注册，请先注册账号"}

            # 5. 自动注册新用户
            try:
                user = create_user_callback(identifier)

                # 6. 自动登录
                from extends.jwt.views import user_login
                data = user_login(user, request)
                return {"success": True, "message": "注册并登录成功", "data": data}

            except Exception as e:
                return {"success": False, "message": f"注册失败: {str(e)}"}

    def _handle_password_reset(self, identifier, code, new_password, find_user_callback):
        """
        处理密码重置的通用逻辑
        :param identifier: 标识符
        :param code: 验证码
        :param new_password: 新密码
        :param find_user_callback: 查找用户的回调函数
        :return: 操作结果
        """
        # 1. 验证验证码
        provider_type = self._get_provider_type()
        is_valid = self.verify_code(identifier, code, provider_type)
        if not is_valid:
            return {"success": False, "message": "验证码错误或已过期"}

        # 2. 验证密码强度
        if not new_password or len(new_password) < 6:
            return {"success": False, "message": "密码长度不能少于6位"}

        # 3. 查找用户
        try:
            user = find_user_callback(identifier)
            if not user:
                return {"success": False, "message": f"该{provider_type}未注册"}

            # 4. 重置密码
            message = user.reset_password(new_password=new_password)
            return {"success": True, "message": message}

        except Exception as e:
            return {"success": False, "message": f"密码重置失败: {str(e)}"}

    def _handle_register(self, identifier, code, username, password, request, find_user_callback, create_user_callback):
        """
        处理注册的通用逻辑
        :param identifier: 标识符
        :param code: 验证码
        :param username: 用户名
        :param password: 密码
        :param request: DRF Request对象
        :param find_user_callback: 查找用户的回调函数
        :param create_user_callback: 创建用户的回调函数
        :return: 注册响应结果
        """
        # 1. 验证验证码
        provider_type = self._get_provider_type()
        is_valid = self.verify_code(identifier, code, provider_type)
        if not is_valid:
            return {"success": False, "message": "验证码错误或已过期"}

        # 2. 检查标识符是否已注册
        if find_user_callback(identifier):
            return {"success": False, "message": f"该{provider_type}已被注册，请直接登录"}

        # 3. 处理用户名
        if username and username.strip():
            # 用户传了用户名，检查是否已存在
            if User.objects.filter(username=username).exists():
                return {"success": False, "message": "该用户名已被使用"}
            final_username = username
        else:
            # 用户没传用户名，自动生成
            final_username = self._generate_unique_username(
                identifier.split('@')[0] if '@' in identifier else identifier
            )

        # 4. 创建新用户
        try:
            user = create_user_callback(final_username, identifier)

            # 设置密码（如果提供了）
            if password:
                user.reset_password(new_password=password)


            # 5. 自动登录
            from extends.jwt.views import user_login
            data = user_login(user, request)
            return {"success": True, "message": "注册成功", "data": data}

        except Exception as e:
            return {"success": False, "message": f"注册失败: {str(e)}"}

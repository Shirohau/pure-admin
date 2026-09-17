import json
import re

from django.utils.deprecation import MiddlewareMixin
from django.db import transaction
from rest_framework.response import Response as DRFResponse
from apps.system.models.log_login.signals import get_ip_address
from apps.system.models.log_request.models import LogRequestModel

# 定义不需要记录日志的 URL 路径（支持正则）
IGNORED_URL_PATTERNS = [
    r'^/api/token/$',  # 登录
    r'^/api/system/menu/routes/$',  # 路由
    r'^/api/system/config/get_config/$',  # 配置文件
    r'^/api/system/log_request/$',  # 查询 请求日志
    r'^/api/system/log_login/$',  # 查询 登录日志
    r'^/api/otp/send-code/$',  # 发送短信，邮箱验证码
    r'^/api/oauth2/get_config/$',  # 第三方登录
    r'^/api/oauth2/callback/$',  # 第三方登录回调
    r'^/health/$',  # 健康检查点
    r'^/static/.*',  # 静态文件（通常不会走到这里，但保险起见）
    r'^/favicon\.ico$',  # favicon
]


class RequestLogMiddleware(MiddlewareMixin):
    @staticmethod
    def process_response(request, response):
        # 获取 URL
        url = request.path

        # === 跳过忽略的 URL ===
        for pattern in IGNORED_URL_PATTERNS:
            if re.match(pattern, url):
                return response  # 不记录，直接返回

        # 只记录成功请求
        if not (200 <= response.status_code < 300):
            return response

        # 获取请求反馈
        feedback = ""
        if isinstance(response, DRFResponse):
            message = response.data.get("message") if hasattr(response.data, 'get') else None
            feedback = str(message) if message is not None else ""

        # 获取用户名（JWT 认证后，user 已设置）
        username = "匿名用户"
        if hasattr(request, 'user') and request.user.is_authenticated:
            username = request.user.name

        # 获取 IP
        ip_address = get_ip_address(request)

        # 获取方法
        method = request.method

        # 获取查询参数（仅 GET）
        query_params = request.GET.dict() if request.GET else {}
        query_params = json.dumps(query_params, ensure_ascii=False, sort_keys=True)
        # 保存数据到数据库
        data = {
            "username": username,
            "ip_address": ip_address,
            "url": url,
            "method": method,
            "feedback": feedback,
            "query_params": query_params
        }
        # 异步安全：使用 transaction.on_commit 确保只在成功时记录
        if hasattr(transaction, 'on_commit'):
            transaction.on_commit(
                lambda: LogRequestModel.objects.create(**data)
            )
        else:
            # 同步环境直接保存
            LogRequestModel.objects.create(**data)

        return response

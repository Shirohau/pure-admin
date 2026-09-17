#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：response.py
@Author  ：李小涛
@Date    ：2025/11/27 上午10:56 
@Explain : 自定义响应：统一成功/失败响应格式与全局异常处理器
"""

from django.http import Http404
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.exceptions import APIException as DRFAPIException

# ===========================================================================
# 业务状态码常量（前后端约定，勿随意修改）
# ===========================================================================
CODE_SUCCESS = 2000  # 成功
CODE_ERROR = 4000  # 通用业务错误
CODE_UNAUTHENTICATED = 4001  # 未登录
CODE_INVALID_TOKEN = 4002  # token 无效或过期
CODE_VALIDATION_ERROR = 4003  # 数据验证失败 / 资源不存在

# ===========================================================================
# 默认提示信息常量
# ===========================================================================
DEFAULT_SUCCESS_MESSAGE = "成功响应"
DEFAULT_ERROR_MESSAGE = "错误响应"
MESSAGE_UNAUTHENTICATED = "未登录"
MESSAGE_INVALID_TOKEN = "无效的token"
MESSAGE_VALIDATION_ERROR = "数据验证失败"
MESSAGE_NOT_FOUND = "权限不够，找不到资源"


def success_response(code=CODE_SUCCESS, message=DEFAULT_SUCCESS_MESSAGE, paginated=None, data=None, summary=None):
    """
    构建统一格式的成功响应

    Args:
        code: 业务状态码（默认 CODE_SUCCESS=2000）
        message: 提示信息（默认 "成功响应"）
        paginated: 分页元数据（分页接口传入，非分页接口为 None）
        data: 业务数据
        summary: 表尾合计

    Returns:
        Response: 统一格式 {"success": True, "code": ..., "message": ..., "paginated": ..., "data": ...}
    """
    return Response({
        "success": True,
        "code": code,
        "message": message,
        "paginated": paginated,
        "data": data,
        "summary": summary,
    })


def error_response(code=CODE_ERROR, message=DEFAULT_ERROR_MESSAGE, data=None):
    """
    构建统一格式的失败响应

    Args:
        code: 业务状态码（默认 CODE_ERROR=4000）
        message: 提示信息（默认 "错误响应"）
        data: 实际的业务处理异常详情

    Returns:
        Response: 统一格式 {"success": False, "code": ..., "message": ..., "data": ...}
    """
    return Response({
        "success": False,
        "code": code,
        "message": message,
        "data": data,
    })


def custom_exception_handler(exc, context):
    """
    自定义全局异常处理器：将 DRF 标准异常统一包装为项目错误响应格式

    处理流程：
        1. 调用 DRF 默认异常处理器，得到标准 Response；
        2. 按异常类型映射业务状态码与提示信息；
        3. 用 error_response 包装后返回。

    Args:
        exc: 捕获到的异常实例
        context: 异常发生时的上下文（视图、请求等）

    Returns:
        Response | None: 统一错误格式响应；DRF 无法处理的异常返回 None（交给 Django 500 处理）
    """
    # 调用 DRF 默认处理器，仅当它能处理该异常时返回 Response
    response = exception_handler(exc, context)
    if response is None:
        return None

    # 提取 DRF 原始错误详情；字符串形式的错误无法作为结构化 data，置为 None
    details = response.data if not isinstance(response.data, str) else None

    # 按异常类型映射业务状态码与提示信息
    if isinstance(exc, NotAuthenticated):
        message = MESSAGE_UNAUTHENTICATED
        code = CODE_UNAUTHENTICATED
    elif isinstance(exc, InvalidToken):
        message = MESSAGE_INVALID_TOKEN
        code = CODE_INVALID_TOKEN
    elif isinstance(exc, ValidationError):
        # message = MESSAGE_VALIDATION_ERROR
        code = CODE_VALIDATION_ERROR
        message = exc.detail
        if isinstance(message, dict):
            for k, v in message.items():
                for i in v:
                    message = "%s:%s" % (k, i)
    elif isinstance(exc, Http404):
        # 不暴露资源是否真实存在，统一提示"找不到资源"（防信息泄露）
        message = MESSAGE_NOT_FOUND
        code = CODE_VALIDATION_ERROR
    else:
        # 其他 DRF 已处理的异常：优先取 detail 字段，否则回退为异常原文
        message = response.data.get("detail", str(exc)) if hasattr(response.data, "get") else str(response.data)
        code = CODE_ERROR

    # 返回统一错误格式
    return error_response(code=code, message=message, data=details)

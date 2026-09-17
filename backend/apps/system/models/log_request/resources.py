#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：resources.py
@Author  ：李小涛
@Date    ：2026/8/3
@Explain : 请求日志导入导出资源（同步/异步通用）
"""
from extends.drf.resources import CustomCeleryResource
from .filters import LogRequestFilter
from .models import LogRequestModel


class LogRequestResource(CustomCeleryResource):
    """请求日志导入导出资源（同步/异步通用）"""

    filterset_class = LogRequestFilter

    class Meta:
        model = LogRequestModel

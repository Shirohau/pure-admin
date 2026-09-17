#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：resources.py
@Author  ：李小涛
@Date    ：2026/8/3
@Explain : 文件管理导入导出资源（同步/异步通用）
"""
from extends.drf.resources import CustomCeleryResource
from .filters import FileFilter
from .models import FileModel


class FileResource(CustomCeleryResource):
    """文件管理导入导出资源（同步/异步通用）"""

    filterset_class = FileFilter

    class Meta:
        model = FileModel

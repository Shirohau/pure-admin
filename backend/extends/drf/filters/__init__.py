#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：__init__.py
@Author  ：李小涛
@Date    ：2026/7/30
@Explain : filters 包 — 提供增强型 FilterSet 基类

本包提供：
    CustomFilter — 增强型 django-filter FilterSet 基类，
                   自动支持动态 __lookup 查询参数解析。

模块组成：
    base.py      — CustomFilter 类定义及 Q 对象构建工具
    parser.py    — URL 查询参数解析（查找表达式提取、字段校验、值转换）
    constants.py — 查询表达式白名单及分类常量

使用方式：
    from extends.drf.filters import CustomFilter

    class UserFilter(CustomFilter):
        '''用户模型筛选器 — 自动支持所有 __lookup 查询'''
        class Meta(CustomFilter.Meta):
            model = UserModel
            # fields 默认为 "__all__"，可按需覆盖

    class UserViewSet(ModelViewSet):
        queryset = UserModel.objects.all()
        filterset_class = UserFilter
"""

from .base import CustomFilter

__all__ = [
    'CustomFilter',
]

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
部门筛选器：继承 CustomFilter 基类，自动支持动态 __lookup 查询参数。

支持的查询参数示例：
    - ?name__icontains=研发      → 部门名称模糊匹配
    - ?status=true               → 按状态精确过滤（树接口状态切换）
    - ?code__icontains=100       → 部门编号模糊匹配

说明：无需逐个声明字段筛选，CustomFilter 会自动为模型全部字段生成
默认 filter，并解析 URL 中未声明的 __lookup 动态参数（详见
extends/drf/filters/base.py）。
"""

from extends.drf.filters import CustomFilter
from .models import DeptModel


class DeptFilter(CustomFilter):
    """部门模型筛选器（全部字段自动支持动态筛选）。"""

    class Meta(CustomFilter.Meta):
        model = DeptModel

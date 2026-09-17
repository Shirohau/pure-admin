#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：filters.py
@Author  ：李小涛
@Date    ：2025/11/29 上午11:49 
@Explain : 图书筛选
"""

from extends.drf.filters import CustomFilter
from .models import BookModel


class BookFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = BookModel

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：serializers.py
@Explain : 流程信息序列化器（与 AntFlow-Designer 数据契约对齐）
"""
from extends.drf.serializers import CustomSerializer
from rest_framework import serializers

from .models import FlowInfoModel


class FlowInfoSerializer(CustomSerializer):
    """流程信息-完整序列化器"""

    class Meta:
        model = FlowInfoModel
        fields = '__all__'

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：serializers.py.py
@Author  ：李小涛
@Date    ：2025/12/1 下午8:15 
@Explain : OAuth2 序列化器
"""

from rest_framework import serializers
from .models import UserOAuthModel


class UserOAuthSerializer(serializers.ModelSerializer):
    """用户第三方账号绑定序列化器"""
    
    # 只读字段：显示平台中文名称
    platform_display = serializers.CharField(
        source='get_platform_display', 
        read_only=True,
        label='平台名称'
    )
    
    # 只读字段：显示用户名
    username = serializers.CharField(
        source='user.name',
        read_only=True,
        label='用户名'
    )
    
    class Meta:
        model = UserOAuthModel
        fields = [
            'id',
            'user',
            'username',
            'platform',
            'platform_display',
            'uid',
            'uname',
            'create_dt',
            'update_dt',
        ]
        read_only_fields = [
            'id', 
            'create_dt', 
            'update_dt',
            'platform_display',
            'username',
        ]

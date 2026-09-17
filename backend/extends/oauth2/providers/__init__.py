#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：__init__.py.py
@Author  ：李小涛
@Date    ：2025/12/12 下午2:35 
@Explain :
"""
# oauth/providers/__init__.py
"""
自动发现并注册所有 OAuth 平台实现
使用方式:
    from . import PROVIDERS
    provider = PROVIDERS['weibo']
"""

import os
import importlib
from typing import Dict, Type
from .base import OAuthProvider

# 全局 Provider 注册表（存储的是类，不是实例）
PROVIDERS: Dict[str, Type[OAuthProvider]] = {}

# 获取当前目录所有 .py 文件（排除 __init__.py、base.py）
provider_files = [
    f[:-3] for f in os.listdir(os.path.dirname(__file__))
    if f.endswith('.py') and f not in ['__init__.py', 'base.py']
]

for module_name in provider_files:
    try:
        # 动态导入模块
        module = importlib.import_module(f'.{module_name}', package=__package__)
        # 查找继承 OAuthProvider 的类
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                    isinstance(attr, type)
                    and issubclass(attr, OAuthProvider)
                    and attr != OAuthProvider
            ):
                # 从类名推断平台名 (WeiboProvider -> 'weibo')
                platform_name = attr_name.replace('Provider', '').lower()
                PROVIDERS[platform_name] = attr
                break
    except Exception as e:
        # 记录加载失败的模块（生产环境可改为 logger.error）
        print(f"Failed to load OAuth provider {module_name}: {e}")

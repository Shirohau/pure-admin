#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/12/1 下午5:55 
@Explain :
"""
from application import settings

# ********** 注册APP **********
settings.INSTALLED_APPS += ['extends.Jinja2']

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：celery.py
@Author  ：李小涛
@Date    ：2025/11/29 下午9:07 
@Explain :
"""

import os


from celery import Celery, platforms
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "application.settings")
# 创建 Celery 实例
app = Celery("dvd")
# 加载配置文件中的 Celery 配置，必须以CELERY_开头，防止冲突
app.config_from_object("django.conf:settings", namespace="CELERY")
# 自动从Django的已注册app中发现任务
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
# 允许使用root用户启动
platforms.C_FORCE_ROOT = True




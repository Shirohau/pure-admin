#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/11/29 下午9:08 
@Explain :
"""

from application import settings

# ********** 注册APP **********
settings.INSTALLED_APPS += ["django_celery_beat", "django_celery_results", "extends.celery", ]

# ********** 注册中间件 **********
# settings.MIDDLEWARE += []

# ********** 注册路由 **********
settings.PLUGINS_URL_PATTERNS += [{"path": r'api/celery/', "include": "extends.celery.urls"}]

# ********** 注册配置 **********

# 使用数据库作为结果后端
CELERY_RESULT_BACKEND = "django-db"
# 启用结果持久化
CELERY_RESULT_PERSISTENT = True
# 启用后才会记录 task_name、date_started 等字段
CELERY_RESULT_EXTENDED = True
# 使用数据库调度器
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
# 消息代理地址
CELERY_BROKER_URL = f"{settings.REDIS_URL}/2",
# 时区的问题
CELERY_TIMEZONE = settings.TIME_ZONE
# 是否使用UTC时间
CELERY_ENABLE_UTC = True
# 是否启用时区感知
DJANGO_CELERY_BEAT_TZ_AWARE = True
# 避免celery启动时，连接redis失败
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# 每个worker最多执行的任务数，超过这个就将worker进行销毁，防止内存泄漏
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
# 单个任务运行的最大时间，超过这个时间，task就会被kill 单位是秒
CELERY_TASK_TIME_LIMIT = 3600  # 1小时
# 记录任务开始时间
CELERY_TASK_TRACK_STARTED = True

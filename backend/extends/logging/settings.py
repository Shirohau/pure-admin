#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/12/1 下午2:34 
@Explain :
"""

import os

from application.settings import BASE_DIR

LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)  # 确保日志目录存在，exist_ok 避免异常

# 定义日志文件路径
SERVER_LOGS_FILE = os.path.join(LOGS_DIR, "server.log")
ERROR_LOGS_FILE = os.path.join(LOGS_DIR, "error.log")

# ------------------- 日志格式定义 -------------------
# 标准日志格式：[时间][模块.函数():行号] [级别] 日志内容
# 示例: [2025-09-14 16:20:00][micoservice.apps.ready():16] [INFO] 这是一条日志
STANDARD_LOG_FORMAT = (
    "[%(asctime)s][%(name)s.%(funcName)s():%(lineno)d] [%(levelname)s] %(message)s"
)
# ------------------- 日志配置字典 -------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # 不禁用其他日志器，避免意外行为

    # 格式化器：定义日志输出样式
    "formatters": {
        "standard": {
            "format": STANDARD_LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",  # 时间格式化
        },
        "console": {
            "format": STANDARD_LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "file": {
            "format": STANDARD_LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },

    # 处理器：定义日志如何处理（输出到哪、级别、格式等）
    "handlers": {
        # 处理普通日志（INFO 及以上），轮转写入文件
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",  # 轮转日志文件
            "filename": SERVER_LOGS_FILE,
            "maxBytes": 1024 * 1024 * 100,  # 单文件最大 100MB
            "backupCount": 5,  # 最多保留 5 个备份文件（如 server.log.1 ~ server.log.5）
            "formatter": "file",
            "encoding": "utf-8",  # 支持中文日志
        },
        # 专门处理错误日志（ERROR 及以上）
        "error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": ERROR_LOGS_FILE,
            "maxBytes": 1024 * 1024 * 100,  # 100MB
            "backupCount": 3,  # 错误日志保留 3 个备份
            "formatter": "standard",
            "encoding": "utf-8",
        },
        # 控制台输出（开发/调试时查看）
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },

    # 日志记录器：定义不同模块的日志行为
    "loggers": {
        # 根日志器：所有未指定的日志都会走这里
        "": {
            "handlers": ["console", "file", "error"],
            "level": "INFO",
            "propagate": False,  # 不向上传播到父 logger
        },
        # Django 核心日志
        "django": {
            "handlers": ["console", "file", "error"],
            "level": "INFO",
            "propagate": False,
        },
        # Django 数据库查询日志（可用于调试 SQL）
        "django.db.backends": {
            "handlers": ["file"],  # 通常不打印到控制台，避免刷屏
            "level": "INFO",
            "propagate": False,
        },
        # Uvicorn 服务器错误日志（ASGI 服务器如 FastAPI）
        "uvicorn.error": {
            "handlers": ["console", "file", "error"],
            "level": "INFO",
            "propagate": False,
        },
        # Uvicorn 访问日志（HTTP 请求）
        "uvicorn.access": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

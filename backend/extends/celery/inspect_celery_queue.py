#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：inspect_celery_queue.py
@Author  ：李小涛
@Date    ：2025/11/30 下午2:49 
@Explain : 查看celery队列中 有多少任务
"""
import redis
import json
import base64
from kombu.serialization import loads

# 连接 Redis DB=2
r = redis.Redis(host='127.0.0.1', port=6379, db=2)

queue_name = "celery"

tasks = r.lrange(queue_name, 0, -1)
print(f"共 {len(tasks)} 个任务在队列 '{queue_name}' 中：\n")

for i, task in enumerate(tasks):
    print(f"\n--- 任务 {i + 1} ---")
    msg_str = task.decode('utf-8')
    msg = json.loads(msg_str)

    # ✅ 函数名在 headers 里！
    task_name = msg["headers"].get("task", "UNKNOWN")
    task_id = msg["headers"].get("id", "N/A")

    # 解析 body: (args, kwargs, embed)
    body_b64 = msg["body"]
    body_bytes = base64.b64decode(body_b64)

    content_type = msg.get("content-type", "application/json")
    content_encoding = msg.get("content-encoding", "utf-8")

    try:
        # body 是一个三元组: (args, kwargs, embed)
        args, kwargs, embed = loads(body_bytes, content_type, content_encoding)
    except Exception as e:
        args, kwargs, embed = [], {}, {}

    print(f"任务 ID     : {task_id}")
    print(f"任务函数    : {task_name}")  # ← 正确位置！
    print(f"参数 args   : {args}")
    print(f"参数 kwargs : {kwargs}")
    if embed and any(embed.values()):
        print(f"嵌入信息    : {embed}")

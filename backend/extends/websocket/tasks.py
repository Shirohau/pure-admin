#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：tasks.py
@Author  ：李小涛
@Date    ：2025/11/29 下午9:15 
@Explain :
"""

import time

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.core.cache import cache

# tasks.py
from celery import shared_task
import time
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@shared_task
def broadcast_to_chat_room(room_name, message, sender="System"):
    """向指定聊天室广播消息"""
    time.sleep(2)  # 模拟耗时
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{room_name}",
        {
            "type": "chat.message",
            "message": message,
            "username": sender,
        }
    )
    return "Message broadcasted"

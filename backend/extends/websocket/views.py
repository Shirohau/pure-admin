#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：consumers.py
@Author  ：李小涛
@Date    ：2025/12/1 下午1:12 
@Explain : WebSocket 消费者
"""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging

from rest_framework_simplejwt.tokens import AccessToken

from application import settings

logger = logging.getLogger(__name__)

User = get_user_model()


class InfraConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 当客户端尝试连接时
        # 获取参数
        query_params = self.scope["query_string"].decode()
        # 从查询参数获取 token
        token_param = [
            param.split("=")
            for param in query_params.split("&")
            if param.startswith("token=")
        ]
        if not token_param or len(token_param[0]) != 2:
            logger.error("缺少token参数")
            await self.close(code=4001)  # 自定义错误码
            return

        token = token_param[0][1]
        try:
            # 验证 Access Token 有效性
            access_token = AccessToken(token)
            user_id = access_token["user_id"]

            # ✅ 异步获取 User 实例
            user = await User.objects.aget(id=user_id)
            # ✅ 将真实的 User 实例赋值给 scope["user"]
            self.scope["user"] = user
            logger.info(f"🤝 认证用户：{user.username} 连接成功, 用户ID: {user_id}")

            # 登录成功后，将用户通道写入缓存
            cache.set(f"user_{user.id}_channel", self.channel_name, timeout=None)  # 可设置超时

            # 加入默认组
            self.scope["room_group_name"] = settings.DEFAULT_GROUP_NAME
            await self.channel_layer.group_add(self.scope["room_group_name"], self.channel_name)

            # 接受连接
            await self.accept()
        except TokenError as e:
            logger.error(f"无效的 Access Token: {e}")
            await self.close(code=4003)  # 无效 token
        except User.DoesNotExist as e:
            logger.error(f"用户不存在，user_id：{e}")
            await self.close(code=4002)  # 用户不存在
        except Exception as e:
            logger.error(f"WebSocket 连接异常: {str(e)}")
            await self.close(code=4000)  # 服务器错误

    async def disconnect(self, close_code):
        # 当客户端断开连接时
        print(f"❌ 用户断开: {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                data = json.loads(text_data)
                message = data.get('message', '')

                logger.info(f"📩 收到消息: {message}")

                # 回 echo 消息
                await self.send(text_data=json.dumps({
                    'reply': f"Server got: {message}",
                    'timestamp': timezone.now().isoformat()
                }))

            except json.JSONDecodeError:
                # ✅ 如果是 ping/pong 心跳包，直接忽略或回复 pong
                if text_data.strip().lower() == 'ping':
                    await self.send(text_data='pong')
                    return

                # 其他非法 JSON
                await self.send(text_data=json.dumps({
                    "error": "Invalid JSON"
                }))
                logger.warning(f"收到无效 JSON 消息: {text_data}")

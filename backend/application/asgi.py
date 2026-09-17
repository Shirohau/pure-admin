"""
ASGI config for application project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""
import os
from django.core.asgi import get_asgi_application
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "application.settings")

# Step 1: 初始化 Django
django_app = get_asgi_application()

# Step 2: 现在可以安全导入 Channels 和路由
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from extends.websocket.urls import websocket_urlpatterns
from extends.oa_sso.websocket import OaSsoWebSocket

# Step 3: 构建完整 ASGI 应用
application = ProtocolTypeRouter({
    "http": Starlette(routes=[
        # # 挂载静态文件到 /static
        # Mount("/static", app=StaticFiles(directory="static"), name="static"),
        # # 挂载用户上传的文件到 /media
        # Mount("/media", app=StaticFiles(directory="media"), name="media"),
        # 其他 HTTP 请求交给 Django 处理
        Mount("/", app=django_app),
    ]),
    "websocket": OaSsoWebSocket(AuthMiddlewareStack(URLRouter(websocket_urlpatterns))),
})

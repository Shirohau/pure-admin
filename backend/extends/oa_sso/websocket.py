"""已有 WebSocket 复用原逻辑；OA 登录额外校验连接及消息时的授权。"""
import time
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from .service import require_session


class OaSsoWebSocket:
    def __init__(self, application):
        self.application = application

    async def __call__(self, scope, receive, send):
        raw = parse_qs(scope.get('query_string', b'').decode(errors='replace')).get('token', [''])[0]
        try:
            token = await database_sync_to_async(UntypedToken)(raw)
        except (TokenError, ValueError, TypeError):
            token = None
        if token is None or not token.get('oa_sso'):
            return await self.application(scope, receive, send)

        closed = False

        async def allowed():
            nonlocal closed
            if closed:
                return False
            try:
                if token['exp'] <= time.time():
                    raise ValueError()
                await database_sync_to_async(require_session)(token)
                return True
            except Exception:
                closed = True
                await send({'type': 'websocket.close', 'code': 4003})
                return False

        async def checked_receive():
            event = await receive()
            if event['type'] != 'websocket.disconnect' and not await allowed():
                return {'type': 'websocket.disconnect', 'code': 4003}
            return event

        async def checked_send(event):
            if event['type'] in ('websocket.accept', 'websocket.send') and not await allowed():
                return
            if not closed:
                await send(event)

        await self.application(scope, checked_receive, checked_send)

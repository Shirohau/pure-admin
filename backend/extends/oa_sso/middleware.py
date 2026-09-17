"""仅为带 oa_sso 签名声明的本应用令牌增加实时授权检查。"""
import json

from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import TokenError
from . import service as sso


class OaSsoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .views import response
        candidates = []
        authorization = request.headers.get('Authorization', '')
        if authorization.startswith('Bearer '):
            candidates.append(authorization[7:])
        if request.path in ('/api/token/refresh/', '/api/token/verify/') and request.method == 'POST':
            try:
                values = json.loads(request.body) if request.content_type == 'application/json' else request.POST
                if isinstance(values, dict) or hasattr(values, 'get'):
                    candidates.extend([values.get('refresh'), values.get('token')])
            except (ValueError, UnicodeDecodeError):
                pass
        for raw in candidates:
            if not isinstance(raw, str) or not raw:
                continue
            try:
                token = UntypedToken(raw)
            except TokenError:
                continue  # 原有认证接口负责处理无效的本地 JWT。
            if not token.get('oa_sso'):
                continue
            try:
                sso.require_session(token)
            except sso.SsoError as error:
                return response(message=str(error), status=error.status)
            except Exception:
                return response(message='暂时无法确认 OA 授权', status=503)
        return self.get_response(request)

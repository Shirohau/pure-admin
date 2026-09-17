import functools
import hashlib
import json
import secrets
import time
from base64 import urlsafe_b64encode
from datetime import datetime, timezone

from django.contrib.auth import user_logged_in
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from extends.jwt.views import UserTokenSerializer
from . import service as sso

TXN_COOKIE = '__Host-vdd_oa_txn'
SESSION_COOKIE = '__Host-vdd_oa_session'


def response(data=None, message='成功响应', status=200):
    result = JsonResponse({'success': status == 200, 'code': 2000 if status == 200 else 4000,
                           'message': message, 'data': data}, status=status)
    result['Cache-Control'] = 'no-store'
    result['Pragma'] = 'no-cache'
    result['Referrer-Policy'] = 'no-referrer'
    return result


def endpoint(view):
    @csrf_exempt
    @sensitive_post_parameters()
    @functools.wraps(view)
    def wrapped(request):
        try:
            cfg = sso.config()
            if request.method != 'POST':
                raise sso.SsoError('仅支持 POST 请求', 405)
            if not request.is_secure() or request.headers.get('Origin') != cfg['OA_APP_ORIGIN']:
                raise sso.SsoError('请从应用自己的 HTTPS 页面发起登录', 403)
            if request.content_type != 'application/json' or len(request.body) > 16384:
                raise sso.SsoError('请求格式无效')
            values = json.loads(request.body)
            if not isinstance(values, dict):
                raise sso.SsoError('请求格式无效')
            return view(request, values)
        except sso.SsoError as error:
            return response(message=str(error), status=error.status)
        except Exception:
            return response(message='OA 认证服务暂不可用，请检查配置或稍后重试', status=503)
    return wrapped


def configuration(request):
    if request.method != 'GET':
        return response(message='仅支持 GET 请求', status=405)
    try:
        cfg = sso.config()
        return response({'issuer': cfg['OA_ISSUER']})
    except sso.SsoError as error:
        return response(message=str(error), status=error.status)


@endpoint
def prepare(request, values):
    if values:
        raise sso.SsoError('准备登录不接收身份参数')
    cfg = sso.config()
    verifier, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
    challenge = urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    started = time.time()
    prepared = sso.platform_request('/sso/v1/desktop/auth-requests/', json_body={
        'redirect_uri': cfg['OA_REDIRECT_URI'], 'scope': 'openid tenant',
        'code_challenge': challenge, 'code_challenge_method': 'S256', 'nonce': nonce,
    })
    ttl = int(min(float(prepared['expires_in']), 300) - (time.time() - started))
    request_id = prepared['request_id']
    if ttl <= 0 or not isinstance(request_id, str) or not request_id:
        raise sso.SsoError('OA 登录准备已过期', 409)
    transaction_id = sso.store('transaction', {'request_id': request_id, 'verifier': verifier, 'nonce': nonce}, ttl)
    sso.redis().set(sso.key('pending', transaction_id), 'pending', ex=ttl)
    result = response({'requestId': request_id})
    result.set_cookie(TXN_COOKIE, transaction_id, max_age=ttl, secure=True, httponly=True, samesite='Lax')
    return result


@endpoint
def complete(request, values):
    if set(values) != {'code', 'requestId'} or any(not isinstance(v, str) or not v or len(v) > 4096 for v in values.values()):
        raise sso.SsoError('登录码或请求标识无效')
    txn_id = request.COOKIES.get(TXN_COOKIE)
    pending = sso.read('transaction', txn_id, consume=True)
    if not pending or pending['request_id'] != values['requestId']:
        raise sso.SsoError('登录事务已失效或已使用，请从工作台重新打开', 409)
    access_token, session_id = None, None
    try:
        started = time.time()
        tokens = sso.platform_request('/o/token/', data={
            'grant_type': 'authorization_code', 'code': values['code'],
            'redirect_uri': sso.config()['OA_REDIRECT_URI'], 'code_verifier': pending['verifier'],
        })
        access_token = tokens['access_token']
        if not isinstance(access_token, str) or not access_token:
            raise sso.SsoError('OA 访问令牌无效', 401)
        identity = sso.verify_identity(tokens['id_token'], pending['nonce'])
        sso.context(access_token, identity)
        user = sso.mapped_user(identity)
        end = sso.deadline(tokens, started)
        session_id = secrets.token_urlsafe(32)
        stored = {'identity': {k: identity[k] for k in ('sub', 'tenant_id', 'member_uid', 'sid')},
                  'access_token': access_token, 'user_id': user.pk, 'deadline': end}
        created = sso.redis().eval("""
            if redis.call('GET', KEYS[1]) ~= 'pending' then return 0 end
            redis.call('SET', KEYS[2], ARGV[2], 'EX', ARGV[3])
            redis.call('SET', KEYS[1], ARGV[1], 'KEEPTTL')
            return 1
        """, 2, sso.key('pending', txn_id), sso.key('session', session_id),
            session_id, sso.seal(stored), max(1, int(end - time.time())))
        if not created:
            raise sso.SsoError('登录已取消，请从工作台重新打开', 409)
        # 复用原账号、角色及原登录响应格式；只增加本次 OA 授权会话关联。
        refresh = RefreshToken.for_user(user)
        refresh['oa_sso'] = session_id
        refresh['exp'] = min(refresh['exp'], end)
        access = refresh.access_token
        access['exp'] = min(access['exp'], end)
        OutstandingToken.objects.filter(jti=refresh['jti']).update(
            token=str(refresh), expires_at=datetime.fromtimestamp(refresh['exp'], timezone.utc))
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        sso.require_session(access)
        data = UserTokenSerializer(user, context={'request': request, 'refresh_token': refresh, 'access_token': access}).data
        sso.end_session(request.COOKIES.get(SESSION_COOKIE))
        result = response(data, '登录成功')
        result.set_cookie(SESSION_COOKIE, session_id, max_age=max(1, int(end - time.time())),
                          secure=True, httponly=True, samesite='Lax')
        result.delete_cookie(TXN_COOKIE, samesite='Lax')
        return result
    except Exception:
        if session_id:
            sso.end_session(session_id)
        if access_token:
            sso.queue_revoke(access_token)
        raise


@endpoint
def logout(request, values):
    if values:
        raise sso.SsoError('退出不接收身份参数')
    # 覆盖“兑换尚未返回时退出”的情况，不允许随后创建出有效会话。
    txn_id = request.COOKIES.get(TXN_COOKIE)
    if sso.identifier_valid(txn_id):
        sso.redis().eval("""
            local session = redis.call('GET', KEYS[1])
            if session and session ~= 'pending' then
                local value = redis.call('GET', ARGV[1] .. session)
                if value then
                    redis.call('HSET', KEYS[3], session, value)
                    redis.call('DEL', ARGV[1] .. session)
                end
            end
            redis.call('DEL', KEYS[1], KEYS[2])
        """, 3, sso.key('pending', txn_id), sso.key('transaction', txn_id),
            sso.key('revocations'), sso.key('session'))
    sso.end_session(request.COOKIES.get(SESSION_COOKIE))
    result = response(message='已退出本应用')
    result.delete_cookie(SESSION_COOKIE, samesite='Lax')
    result.delete_cookie(TXN_COOKIE, samesite='Lax')
    return result

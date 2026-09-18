"""只处理 OA 登录；平台长期凭据保留在后台，验证身份后自动创建普通账号。"""
import base64
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import time
from functools import lru_cache
from urllib.parse import quote_plus, urlsplit

import jwt
import requests
from Crypto.Cipher import AES
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django_redis import get_redis_connection

from extends.oauth2.models import UserOAuthModel
from .constants import OA_BINDING_PLATFORM


class SsoError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def enabled():
    return os.getenv('OA_SSO_ENABLED', '0') == '1'


@lru_cache(maxsize=1)
def config():
    if not enabled():
        raise SsoError('OA 免登尚未配置', 503)
    values = {name: os.getenv(name, '').strip() for name in (
        'OA_ISSUER', 'OA_CLIENT_ID', 'OA_CLIENT_SECRET', 'OA_REDIRECT_URI',
        'OA_APP_ORIGIN', 'OA_STORE_ENCRYPTION_KEY',
    )}
    values['test_mode'] = os.getenv('OA_SSO_TEST_MODE', '0') == '1'
    try:
        if values['test_mode'] and not values['OA_APP_ORIGIN']:
            redirect = urlsplit(values['OA_REDIRECT_URI'])
            values['OA_APP_ORIGIN'] = f'{redirect.scheme}://{redirect.netloc}'
        for name in ('OA_ISSUER', 'OA_APP_ORIGIN', 'OA_REDIRECT_URI'):
            value = urlsplit(values[name])
            if value.scheme != 'https' or not value.netloc or value.username or value.password or value.fragment:
                raise ValueError()
            if name != 'OA_REDIRECT_URI' and (value.path not in ('', '/') or value.query):
                raise ValueError()
        for name in ('OA_ISSUER', 'OA_APP_ORIGIN'):
            values[name] = values[name].rstrip('/')
        if urlsplit(values['OA_REDIRECT_URI']).netloc != urlsplit(values['OA_APP_ORIGIN']).netloc:
            raise ValueError()
        if not values['OA_CLIENT_ID'] or not values['OA_CLIENT_SECRET']:
            raise ValueError()
        if values['test_mode'] and not values['OA_STORE_ENCRYPTION_KEY']:
            # 测试部署复用稳定的 Django 密钥，但为此应用单独派生加密用途的密钥。
            # 已有显式配置始终优先，避免使此前保存的会话无法解密。
            secret = os.getenv('DJANGO_SECRET_KEY', '')
            if not secret:
                raise ValueError()
            purpose = 'vdd:oa-sso:test-storage:v1\n' + values['OA_ISSUER'] + '\n' + values['OA_CLIENT_ID']
            values['key'] = hmac.new(secret.encode(), purpose.encode(), hashlib.sha256).digest()
        else:
            if not re.fullmatch(r'[0-9a-fA-F]{64}', values['OA_STORE_ENCRYPTION_KEY']):
                raise ValueError()
            values['key'] = bytes.fromhex(values['OA_STORE_ENCRYPTION_KEY'])
    except (ValueError, TypeError, KeyError):
        raise SsoError('OA 免登配置不完整，请联系应用管理员', 503) from None
    return values


def key(kind, identifier=''):
    cfg = config()
    namespace = hashlib.sha256((cfg['OA_ISSUER'] + '\n' + cfg['OA_CLIENT_ID']).encode()).hexdigest()[:24]
    return f'vdd:oa-sso:{namespace}:{kind}:{identifier}'


def seal(value):
    cipher = AES.new(config()['key'], AES.MODE_GCM)
    cipher.update(key('encryption').encode())
    payload, tag = cipher.encrypt_and_digest(json.dumps(value).encode())
    return base64.b64encode(cipher.nonce + tag + payload)


def unseal(value):
    raw = base64.b64decode(value)
    cipher = AES.new(config()['key'], AES.MODE_GCM, nonce=raw[:16])
    cipher.update(key('encryption').encode())
    return json.loads(cipher.decrypt_and_verify(raw[32:], raw[16:32]))


def redis():
    return get_redis_connection('default')


def store(kind, value, ttl):
    identifier = secrets.token_urlsafe(32)
    redis().set(key(kind, identifier), seal(value), ex=max(1, int(ttl)), nx=True)
    return identifier


def identifier_valid(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-]{43}', value) is not None


def read(kind, identifier, consume=False):
    if not identifier_valid(identifier):
        return None
    connection = redis()
    raw = connection.getdel(key(kind, identifier)) if consume else connection.get(key(kind, identifier))
    return unseal(raw) if raw else None


def platform_failure(response, path, *, authenticated=False):
    """只展示协议错误编号，不透传可能含凭据或代理页面内容的原始响应。"""
    stage = {
        '/sso/v1/desktop/auth-requests/': '准备登录',
        '/o/token/': '兑换登录码',
        '/o/jwks/': '读取身份验签公钥',
        '/sso/v1/tenant-context/': '确认员工与企业身份',
        '/o/revoke/': '撤销应用授权',
    }.get(path, '调用认证服务')
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    reason = payload.get('reason_code') or payload.get('error')
    if not isinstance(reason, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,79}', reason):
        reason = 'unknown_error'
    request_id = payload.get('request_id')
    if not isinstance(request_id, str) or not re.fullmatch(r'[0-9a-f]{24}', request_id):
        request_id = None
    hints = {
        'https_required': 'ECP 后台未识别到 HTTPS，请检查 ECP 平台的代理转发配置',
        'client_authentication_required': 'ECP 未收到客户端认证信息，请检查平台代理是否保留 Authorization',
        'client_authentication_invalid': 'Client ID 或 Client Secret 不匹配，请核对当前 ECP 平台为此应用签发的凭据',
        'invalid_client': '客户端认证失败，请核对应用凭据',
        'client_credential_inactive': '应用凭据已过期或被撤销，请更新凭据',
        'redirect_uri_invalid': 'OA_REDIRECT_URI 与 ECP 登记的完整回调地址不一致',
        'enterprise_redirect_uri_invalid': '回调地址不在企业批准的地址中',
        'scope_not_allowed': '客户端未允许所需身份范围，请检查 openid、tenant；非测试模式还需 profile',
        'application_not_published': '应用尚未发布或已暂停，请检查 ECP 应用发布状态',
        'server_ip_not_allowed': '外接应用服务器的出口 IP 不在 ECP 应用的 IP 白名单中',
        'protocol_disabled': 'ECP 平台尚未开启外部认证',
        'enterprise_registration_required': '企业尚未批准此应用接入',
        'signing_key_missing': 'ECP 平台未配置身份令牌签名私钥',
        'signing_key_invalid': 'ECP 平台无法读取有效的身份令牌签名私钥',
        'code_invalid': '登录码无效、已过期或已使用，请从工作台重新打开',
        'code_binding_mismatch': '登录码对应的应用或回调地址不匹配',
        'authentication_store_unavailable': 'ECP 认证数据服务暂不可用，请检查平台日志',
    }
    expired = authenticated and response.status_code in (401, 403)
    hint = hints.get(reason, 'OA 授权已失效，请重新从工作台打开' if expired
                     else '请根据错误编号检查 ECP 平台响应和应用配置')
    if 300 <= response.status_code < 400:
        hint = '认证接口发生跳转，请检查 OA_ISSUER 和 ECP 网关路由'
    elif response.status_code == 404:
        hint = 'ECP 认证接口不存在，请检查 OA_ISSUER 和 ECP 网关路由'
    detail = f'HTTP {response.status_code}，{reason}'
    if request_id:
        detail += f'，平台请求编号 {request_id}'
    return SsoError(f'OA {stage}失败：{hint}（{detail}）', 401 if expired else 502)


def platform_request(path, *, data=None, json_body=None, access_token=None):
    cfg = config()
    headers = {}
    if access_token:
        headers['Authorization'] = 'Bearer ' + access_token
    elif data is not None or json_body is not None:
        basic = quote_plus(cfg['OA_CLIENT_ID']) + ':' + quote_plus(cfg['OA_CLIENT_SECRET'])
        headers['Authorization'] = 'Basic ' + base64.b64encode(basic.encode()).decode()
    response = requests.request(
        'POST' if data is not None or json_body is not None else 'GET',
        cfg['OA_ISSUER'] + path, data=data, json=json_body, headers=headers,
        timeout=(5, 10), allow_redirects=False,
        verify=os.getenv('OA_CA_BUNDLE') or True,
    )
    if response.status_code != 200:
        raise platform_failure(response, path, authenticated=bool(access_token))
    if path == '/o/revoke/':
        return None
    payload = response.json()
    if not isinstance(payload, dict):
        raise SsoError('OA 平台响应无效', 502)
    return payload


def verify_identity(id_token, nonce):
    cfg = config()
    try:
        header = jwt.get_unverified_header(id_token)
        if header.get('alg') != 'RS256' or not header.get('kid'):
            raise ValueError()
        # 只访问配置 issuer 的公钥地址，不跟随 JWT header 中的 jku/x5u。
        jwks = platform_request('/o/jwks/')
        candidates = [item for item in jwks.get('keys', []) if item.get('kid') == header['kid']
                      and item.get('kty') == 'RSA' and item.get('use', 'sig') == 'sig'
                      and item.get('alg', 'RS256') == 'RS256']
        if len(candidates) != 1:
            raise ValueError()
        public_key = jwt.PyJWK.from_dict(candidates[0], algorithm='RS256').key
        claims = jwt.decode(id_token, public_key, algorithms=['RS256'], issuer=cfg['OA_ISSUER'],
                            audience=cfg['OA_CLIENT_ID'], options={'require': [
                                'iss', 'aud', 'exp', 'iat', 'sub', 'nonce', 'tenant_id', 'sid']})
        if claims.get('nonce') != nonce or 'member_uid' not in claims:
            raise ValueError()
        if any(not isinstance(claims.get(field), str) or not claims[field] for field in ('sub', 'tenant_id', 'sid')):
            raise ValueError()
        if claims['member_uid'] is not None and (not isinstance(claims['member_uid'], str) or not claims['member_uid']):
            raise ValueError()
        if (isinstance(claims['aud'], list) and len(claims['aud']) > 1 or 'azp' in claims) and claims.get('azp') != cfg['OA_CLIENT_ID']:
            raise ValueError()
        return claims
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise SsoError('OA 身份令牌校验失败', 401) from None


def context(access_token, identity):
    result = platform_request('/sso/v1/tenant-context/', access_token=access_token)
    if any(result.get(field) != identity.get(field) for field in ('sub', 'tenant_id', 'member_uid', 'sid')):
        raise SsoError('OA 授权身份不一致', 401)
    return result


def mapped_user(identity, *, create=False, profile_data=None):
    """仅首次成功兑换允许创建；业务请求与刷新令牌只读取已有身份关联。"""
    subject = {'issuer': config()['OA_ISSUER'], 'tenant_id': identity.get('tenant_id'),
               'sub': identity.get('sub')}
    if any(not isinstance(value, str) or not value for value in subject.values()):
        raise SsoError('OA 身份信息不完整', 401)
    uid = hashlib.sha256(json.dumps(subject, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    query = UserOAuthModel.objects.filter(platform=OA_BINDING_PLATFORM, uid=uid)
    binding = query.first()
    if binding is None and create:
        # 姓名和用户名只用于显示；不按邮箱、手机号或同名账号自动合并身份。
        profile_data = profile_data or {}
        name = next((value.strip() for value in (
            profile_data.get('name'), profile_data.get('preferred_username')
        ) if isinstance(value, str) and value.strip()), 'ECP 员工 ' + uid[:8])[:40]
        try:
            with transaction.atomic():
                user = get_user_model()(
                    username='oa_' + secrets.token_hex(24), name=name,
                    is_active=True, is_staff=False, is_superuser=False,
                    email=None, mobile=None,
                )
                user.set_unusable_password()
                user.save(force_insert=True)
                # 表已有 (platform, uid) 唯一约束。并发重复创建失败时同时回滚新用户。
                binding = UserOAuthModel.objects.create(
                    user=user, platform=OA_BINDING_PLATFORM, uid=uid,
                    uname=name, uinfo={'identity': subject},
                )
        except IntegrityError:
            binding = query.first()
            if binding is None:
                raise
    if binding is None:
        raise SsoError('OA 账号关联已失效，请从工作台重新打开', 401)
    if not isinstance(binding.uinfo, dict) or binding.uinfo.get('identity') != subject:
        raise SsoError('OA 账号关联身份不一致', 401)
    user = get_user_model().objects.filter(pk=binding.user_id, is_active=True).first()
    if user is None:
        raise SsoError('关联的本应用账号不存在或已停用', 403)
    return user


def deadline(tokens, started):
    try:
        fields = ('expires_in', 'authorization_expires_in', 'grant_expires_at', 'session_expires_at', 'idle_expires_at')
        if any(isinstance(tokens[field], bool) or not isinstance(tokens[field], (int, float))
               or not math.isfinite(tokens[field]) or tokens[field] <= 0 for field in fields):
            raise ValueError()
        end = int(min(started + tokens['expires_in'], started + 8 * 3600,
                      tokens['grant_expires_at'], tokens['session_expires_at'], tokens['idle_expires_at']))
        if end <= time.time():
            raise ValueError()
        return end
    except (KeyError, TypeError, ValueError):
        raise SsoError('OA 授权期限无效', 401) from None


def require_session(token):
    session_id = token.get('oa_sso')
    if not session_id:
        return  # 普通账号密码登录保持原认证规则。
    session = read('session', session_id)
    if not session or str(session['user_id']) != str(token.get('user_id')) or session['deadline'] <= time.time():
        raise SsoError('OA 应用会话已失效，请重新从工作台打开', 401)
    context(session['access_token'], session['identity'])
    if mapped_user(session['identity']).pk != session['user_id']:
        raise SsoError('OA 账号关联已变更，请重新登录', 401)
    if not redis().exists(key('session', session_id)):
        raise SsoError('OA 应用会话已退出', 401)


def queue_revoke(access_token):
    job = secrets.token_urlsafe(32)
    redis().hset(key('revocations'), job, seal({'access_token': access_token}))


def end_session(session_id):
    if not identifier_valid(session_id):
        return
    # 删除会话与保存撤销任务同一个 Redis 操作，故障时不丢失待撤销令牌。
    redis().eval("""
        local value = redis.call('GET', KEYS[1])
        if value then
            redis.call('HSET', KEYS[2], ARGV[1], value)
            redis.call('DEL', KEYS[1])
        end
    """, 2, key('session', session_id), key('revocations'), session_id)


def retry_revocations():
    connection = redis()
    _, jobs = connection.hscan(key('revocations'), count=10)
    for job, value in list(jobs.items())[:10]:
        try:
            record = unseal(value)
            platform_request('/o/revoke/', data={'token': record['access_token'], 'token_type_hint': 'access_token'})
            connection.hdel(key('revocations'), job)
        except Exception:
            continue  # 保留队列；不输出包含授权信息的异常。

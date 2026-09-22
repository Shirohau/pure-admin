"""接收加密回调，保存验收记录；不自动修改测试应用的用户或部门。"""
import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import struct
import time
import uuid
from datetime import datetime, timezone

from Crypto.Cipher import AES
from django.core.exceptions import RequestDataTooBig
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django_redis import get_redis_connection
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)
EVENTS = {
    'directory.user.created': '通讯录用户增加',
    'directory.user.updated': '通讯录用户更改',
    'directory.user.resigned': '通讯录用户离职',
    'directory.department.created': '通讯录企业部门创建',
    'directory.department.updated': '通讯录企业部门修改',
    'directory.department.deleted': '通讯录企业部门删除',
}
RETENTION = 7 * 24 * 3600


def configuration():
    app_id = os.getenv('OA_EVENT_APP_ID', '').strip()
    token = os.getenv('OA_EVENT_TOKEN', '').strip()
    aes_key = os.getenv('OA_EVENT_AES_KEY', '').strip()
    if (not re.fullmatch(r'[A-Za-z0-9]{3,32}', token)
            or not re.fullmatch(r'[A-Za-z0-9]{43}', aes_key)):
        raise ValueError('事件配置缺失或格式不正确')
    if str(uuid.UUID(app_id)) != app_id:
        raise ValueError('AppID 格式不正确')
    return app_id, token, base64.b64decode(aes_key + '=', validate=True)


def signature(token, timestamp, nonce, encrypted):
    return hashlib.sha1(''.join(sorted([token, timestamp, nonce, encrypted])).encode()).hexdigest()


def decode(request, app_id, token, aes_key):
    if len(request.body) > 65536:
        raise ValueError('请求过大')
    envelope = json.loads(request.body)
    encrypted = envelope['encrypt']
    timestamp = request.GET.get('timestamp', request.GET.get('timeStamp', ''))
    nonce = request.GET.get('nonce', '')
    supplied = request.GET.get('signature', request.GET.get('msg_signature', ''))
    if (not isinstance(encrypted, str) or not nonce or len(nonce) > 128
            or not re.fullmatch(r'[0-9]{1,13}', timestamp)):
        raise ValueError('信封格式不正确')
    seconds = int(timestamp) / 1000 if len(timestamp) == 13 else int(timestamp)
    if abs(time.time() - seconds) > 300:
        raise ValueError('请求已过期')
    if not hmac.compare_digest(supplied, signature(token, timestamp, nonce, encrypted)):
        raise ValueError('签名不正确')
    padded = AES.new(aes_key, AES.MODE_CBC, aes_key[:16]).decrypt(base64.b64decode(encrypted, validate=True))
    count = padded[-1]
    if not 1 <= count <= 32 or padded[-count:] != bytes([count]) * count:
        raise ValueError('填充不正确')
    framed = padded[:-count]
    if len(framed) < 20:
        raise ValueError('消息长度不正确')
    size = struct.unpack('!I', framed[16:20])[0]
    if size > len(framed) - 20 or framed[20 + size:] != app_id.encode():
        raise ValueError('AppID 不匹配')
    payload = json.loads(framed[20:20 + size])
    if not isinstance(payload, dict) or payload.get('app_id') != app_id:
        raise ValueError('AppID 不匹配')
    if payload.get('EventType') != 'check_url':
        if payload.get('type') not in EVENTS or not isinstance(payload.get('data'), dict):
            raise ValueError('不支持的事件')
        uuid.UUID(payload['id'])
    return payload


def acknowledgement(app_id, token, aes_key):
    framed = secrets.token_bytes(16) + struct.pack('!I', 7) + b'success' + app_id.encode()
    count = 32 - len(framed) % 32
    encrypted = base64.b64encode(AES.new(aes_key, AES.MODE_CBC, aes_key[:16]).encrypt(
        framed + bytes([count]) * count)).decode()
    timestamp, nonce = str(int(time.time() * 1000)), secrets.token_hex(16)
    return {'encrypt': encrypted, 'timeStamp': timestamp, 'nonce': nonce,
            'msg_signature': signature(token, timestamp, nonce, encrypted)}


def receipts_key(app_id):
    return f'vdd:oa-events:{app_id}:receipts'


def record(payload, app_id):
    verification = payload.get('EventType') == 'check_url'
    event_id = str(uuid.uuid4()) if verification else payload['id']
    event_type = 'check_url' if verification else payload['type']
    value = {
        'received_at': datetime.now(timezone.utc).isoformat(), 'app_id': app_id,
        'event_id': event_id, 'event_type': event_type,
        'event_name': '连接验证' if verification else EVENTS[event_type],
        'tenant_id': payload.get('tenant_id'), 'data': payload.get('data', {}),
    }
    # 多个 Django worker 共用 Redis；只有首次收到事件才加入记录。
    # 保存失败不返回 success，让平台重试。记录保留最近 100 条，7 天过期。
    created = get_redis_connection('default').eval('''
        if redis.call('EXISTS', KEYS[1]) == 1 then return 0 end
        redis.call('LPUSH', KEYS[2], ARGV[1])
        redis.call('LTRIM', KEYS[2], 0, 99)
        redis.call('EXPIRE', KEYS[2], ARGV[2])
        redis.call('SET', KEYS[1], '1', 'EX', ARGV[2])
        return 1
    ''', 2, f'vdd:oa-events:{app_id}:seen:{event_id}', receipts_key(app_id),
        json.dumps(value, ensure_ascii=False), RETENTION)
    # 不输出 token、aes_key、签名、密文或业务资料正文。
    logger.info('OA_EVENT %s app_id=%s event_id=%s type=%s',
                'verified' if verification else ('received' if created else 'duplicate'),
                app_id, event_id, event_type)


def response(data, status=200):
    result = JsonResponse(data, status=status)
    result['Cache-Control'] = 'no-store'
    return result


@csrf_exempt
@sensitive_post_parameters()
def callback(request):
    if request.method != 'POST':
        result = response({'error': '仅支持平台发送 POST 回调'}, 405)
        result['Allow'] = 'POST'
        return result
    try:
        cfg = configuration()
    except (ValueError, TypeError):
        return response({'error': '请配置 OA_EVENT_APP_ID、OA_EVENT_AES_KEY、OA_EVENT_TOKEN'}, 503)
    if request.content_type != 'application/json':
        return response({'error': '仅支持 application/json'}, 415)
    try:
        payload = decode(request, *cfg)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, struct.error, RequestDataTooBig):
        return response({'error': '回调验签或解密失败，请检查密钥、AppID 和服务器时间'}, 403)
    try:
        record(payload, cfg[0])
    except RedisError:
        logger.warning('OA_EVENT storage_unavailable')
        return response({'error': '接收记录暂时无法保存，请重试'}, 503)
    return response(acknowledgement(*cfg))

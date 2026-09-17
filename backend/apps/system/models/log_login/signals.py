from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
import requests
from django.conf import settings
from ua_parser import user_agent_parser

from apps.system.models.log_login.models import LogLoginModel


def get_ip_address(request):
    """获取请求的真实 IP 地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For: client, proxy1, proxy2 → 取第一个
        ip = x_forwarded_for.split(',')[0].strip()
        return ip
    # 如果没有 X-Forwarded-For，再尝试 REMOTE_ADDR
    ip = request.META.get('REMOTE_ADDR', '')
    return ip or 'unknown'


def get_ip_analysis(ip):
    """
    获取ip详细概略
    :param ip: ip地址
    :return:
    """
    data = {
        "continent": "",
        "country": "",
        "province": "",
        "city": "",
        "district": "",
        "isp": "",
        "area_code": "",
        "country_english": "",
        "country_code": "",
        "longitude": "",
        "latitude": ""
    }
    if ip != 'unknown' and ip:
        if getattr(settings, 'ENABLE_LOGIN_ANALYSIS_LOG', True):
            try:
                res = requests.get(url='https://ip.django-vue-admin.com/ip/analysis', params={"ip": ip}, timeout=5)
                if res.status_code == 200:
                    res_data = res.json()
                    if res_data.get('code') == 0:
                        data = res_data.get('data')
                return data
            except Exception as e:
                print(e)
    return data


def get_user_agent(request):
    """
    解析请求中的 User-Agent 信息，提取浏览器、操作系统和设备详情

    :param request: HTTP 请求对象，包含 META 信息
    :return: dict，包含以下字段：
        - user_agent: 完整的 User-Agent 字符串
        - browser: 浏览器名称及版本号
        - os_info: 操作系统名称及版本号
        - device: 设备类型
    """
    ua_string = request.META.get('HTTP_USER_AGENT', '')

    # 使用 ua-parser 解析 User-Agent 字符串
    parsed = user_agent_parser.Parse(ua_string)

    # 获取完整的 User-Agent 字符串
    user_agent = parsed.get('string', '')

    # 解析浏览器信息（家族 + 主版本号）
    browser_family = parsed.get('user_agent', {}).get('family') or 'Unknown'
    browser_major = parsed.get('user_agent', {}).get('major')
    if browser_major:
        browser = f"{browser_family} {browser_major}"
    else:
        browser = browser_family

    # 解析操作系统信息（家族 + 主版本号）
    os_family = parsed.get('os', {}).get('family') or 'Unknown'
    os_major = parsed.get('os', {}).get('major')
    if os_major:
        os_info = f"{os_family} {os_major}"
    else:
        os_info = os_family

    # 获取设备类型
    device = parsed.get('device', {}).get('family') or 'Unknown'

    return {
        "user_agent": user_agent,
        "browser": browser,
        "os_info": os_info,
        "device": device,
    }


@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    data = {
        # 边界处理：LogLoginModel.username 字段 max_length=20，
        # 而用户 name 最长 40 字符，超长登录名会触发 MySQL DataError 导致登录 500，故截断写入
        "username": user.name[:20] if user.name else user.username[:20],
        "ip_address": get_ip_address(request),
        "login_time": timezone.now(),
        **get_user_agent(request)
    }
    LogLoginModel.objects.create(**data)

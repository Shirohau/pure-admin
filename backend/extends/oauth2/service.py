# oauth_service.py
"""
OAuth 业务逻辑处理中心。
职责：
- 创建本地用户
- 绑定第三方账号
- 用户登录并签发 JWT Token
- 处理登录/绑定两种场景
"""
import random

from django.contrib.auth import get_user_model
from django.conf import settings
from .models import UserOAuthModel
from extends.drf.response import success_response, error_response
from extends.jwt.views import user_login
from .providers.base import OAuthError
from .config import get_platform_config

# 从 providers 包自动导入所有已注册平台
from .providers import PROVIDERS

User = get_user_model()


def generate_unique_username(base: str) -> str:
    """
    生成唯一用户名，避免冲突。
    策略：先尝试 base_1, base_2... 最多 100 次，之后加随机数防死循环。
    :param base: 基础用户名
    :return: 唯一的用户名
    """
    username = base
    for i in range(1, 101):
        if not User.objects.filter(username=username).exists():
            return username
        username = f"{base}_{i}"
    # 极端情况：加随机后缀
    return f"{base}_{random.randint(1000, 9999)}"


class OAuthService:
    """
    OAuth 服务类：封装登录/绑定全流程。
    初始化参数：
        request: DRF Request对象
    """

    def __init__(self, request):
        self.request = request
        # 提取参数
        self.platform = request.data.get('platform')  # 平台名称 (weibo/gitee/work_weixin)
        self.kind = request.data.get('kind')  # 平台类型 (PC/M)，用于区分不同 redirect_uri
        self.source = request.data.get('source')  # 操作类型 (login/binding)
        self.code = request.data.get('code')  # 授权码
        self.user_id = request.data.get('user_id')  # 当前用户ID（仅 binding 时需要）

        # 验证必要参数
        if not self.platform:
            raise ValueError("缺少必要参数【平台名称】: platform")
        if not self.kind:
            raise ValueError("缺少必要参数【平台类型】: kind")
        if not self.source:
            raise ValueError("缺少必要参数【操作类型】: source")
        if self.source == 'binding' and not self.user_id:
            raise ValueError("绑定操作必须提供当前用户的 user_id")
        # 安全校验：绑定操作必须处于登录态，且 user_id 必须与当前登录用户一致，
        # 防止攻击者用第三方账号 + 任意 user_id 接管目标账户（账户接管漏洞）
        if self.source == 'binding':
            current_user = getattr(self.request, 'user', None)
            if not current_user or not getattr(current_user, 'is_authenticated', False):
                raise ValueError("绑定操作需要先登录")
            try:
                if int(self.user_id) != int(current_user.id):
                    raise ValueError("无权绑定该账户")
            except (TypeError, ValueError):
                raise ValueError("无权绑定该账户")

        # 获取第三方 Provider 类并实例化
        provider_class = PROVIDERS.get(self.platform)
        if not provider_class:
            raise ValueError(f"不支持的 OAuth 平台: {self.platform}")

        # 获取平台配置
        config = get_platform_config(self.platform, self.kind)

        # 注入当前请求的上下文到 第三方 provider 实例
        # 此时 provider_class 已确保不是 None
        self.provider = provider_class(code=self.code, config=config)

        self._existing_oauth = None  # 缓存查询结果
        self.uid = None  # 第三方平台的用户id
        self.uname = None  # 第三方平台显示名
        self.uinfo = None  # 原始用户信息（JSON 格式存入数据库）

    def get_existing_oauth(self):
        """懒加载第三方账号绑定状态（避免重复查询）"""
        if self._existing_oauth is None:
            self._existing_oauth = UserOAuthModel.objects.filter(
                platform=self.platform,
                uid=self.uid
            ).first()
        return self._existing_oauth

    def _create_user(self, base_username: str) -> User:
        """创建新的本地系统用户"""
        username = generate_unique_username(base_username)
        user = User.objects.create(
            username=username,
            name=username,  # 可根据需求补充 email、avatar 等
        )
        self.user_id = user.id
        return user

    def _bind_oauth(self):
        """
        将第三方账号绑定到当前用户。
        使用 update_or_create 避免重复绑定。
        :return: 绑定信息字典
        """
        defaults = {
            "user_id": self.user_id,
            "uname": self.uname,  # 第三方平台显示名
            "uinfo": self.uinfo,  # 原始用户信息（JSON 格式存入数据库）
        }
        social_auth, created = UserOAuthModel.objects.update_or_create(
            platform=self.platform,
            uid=self.uid,
            defaults=defaults
        )

        action = "绑定" if created else "更新"

        # 返回结构化数据供前端使用
        return {
            'id': str(social_auth.id),
            'user_id': str(social_auth.user_id),
            'platform': social_auth.platform,
            'uid': str(social_auth.uid),
            'uname': social_auth.uname,
        }

    def _login_user(self):
        """
        用户登录：更新最后登录时间，并签发 JWT Token。
        :return: 登录响应数据
        """
        try:
            user = User.objects.get(id=self.user_id)
            return user_login(user, self.request)
        except User.DoesNotExist:
            raise ValueError("用户不存在")

    def login_handler(self):
        """
        登录逻辑：
            1. 检查第三方平台账号是否有绑定
            2. 若已绑定，直接登录
            3. 若未绑定：
                - 如果允许自动注册，则创建用户、绑定并登录
                - 否则返回错误，提示需先绑定
        :return: 登录响应
        """
        existing_oauth = self.get_existing_oauth()
        if existing_oauth:
            # 已绑定，直接登录
            self.user_id = existing_oauth.user_id
            data = self._login_user()
            return success_response(message="登录成功", data=data)

        # 未绑定的情况，是否允许注册
        if not getattr(settings, 'AUTO_REGISTER', False):
            return error_response(message=f"{self.platform}账号未绑定，请先在账户设置中绑定")

        # 允许自动注册：创建用户 + 绑定 + 登录
        self._create_user(self.uname or f"{self.platform}_user")
        self._bind_oauth()
        data = self._login_user()
        return success_response(message="注册并登录成功", data=data)

    def binding_handler(self):
        """
        绑定逻辑：
            1、需要获取当前登录用户id
            2、需要获取当前点击的第三方登录平台的用户信息
        :return: 绑定响应
        """
        existing_oauth = self.get_existing_oauth()
        if existing_oauth:
            # 检查是否已经绑定到当前用户
            if existing_oauth.user_id == self.user_id:
                return error_response(message=f"{self.platform}账号已绑定到当前账户")
            return error_response(message=f"{self.platform}账号已绑定其他账户")

        bind_data = self._bind_oauth()
        return success_response(message="绑定成功", data=bind_data)

    def handle(self):
        """
        主入口：仅负责初始化流程和异常处理
        具体业务逻辑委托给场景处理器
        :return: 处理结果响应
        """
        try:
            # 获取第三方平台的用户信息
            user_info = self.provider.get_user_info()
            self.uid = user_info['uid']  # 第三方平台的用户id
            self.uname = user_info['uname']  # 第三方平台显示名
            self.uinfo = user_info['uinfo']  # 原始用户信息（JSON 格式存入数据库）


        except OAuthError as e:
            return error_response(message=e.message)
        except Exception as e:
            return error_response(message=f"获取用户信息失败: {str(e)}")

        handlers = {
            "login": self.login_handler,
            "binding": self.binding_handler,
        }

        handler_fun = handlers.get(self.source)
        if not handler_fun:
            return error_response(message=f"不支持的操作类型: {self.source}")

        return handler_fun()

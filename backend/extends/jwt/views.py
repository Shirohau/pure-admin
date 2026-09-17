#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：views.py
@Author  ：李小涛
@Date    ：2025/10/27 下午2:38 
@Explain : 自定义 token 接口：登录、验证、刷新、在线用户查询、踢用户下线
"""

import logging
from collections import defaultdict

from django.contrib.auth import get_user_model, user_logged_in
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from application import settings
from extends.drf.response import error_response, success_response

# 模块级日志记录器（替代 print，便于统一日志管理）
logger = logging.getLogger(__name__)

# 用户模型（统一入口，避免多处重复调用 get_user_model）
User = get_user_model()

# 在线会话时间的展示格式（统一时间字符串样式）
DATETIME_DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S"

# 会话无法关联用户时的兜底显示名称
UNKNOWN_USER_DISPLAY = "未知用户"


class UserTokenSerializer(serializers.ModelSerializer):
    """
    统一的用户信息序列化器

    用于登录、token 验证、token 刷新等接口返回一致的数据结构。
    token 信息（accessToken / refreshToken / expires）不在模型字段中，
    而是由调用方通过序列化器 context 注入，保证各接口输出格式统一。
    """
    id = serializers.IntegerField(help_text="用户ID")
    accessToken = serializers.SerializerMethodField(help_text="访问令牌")
    refreshToken = serializers.SerializerMethodField(help_text="刷新令牌")
    expires = serializers.SerializerMethodField(help_text="access token 过期时间戳（毫秒）")
    username = serializers.CharField(help_text="用户账号")
    name = serializers.CharField(help_text="用户姓名")
    avatar = serializers.SerializerMethodField(help_text="头像URL")
    roles = serializers.SerializerMethodField(help_text="角色ID列表")
    deptName = serializers.SerializerMethodField(help_text="部门名称")

    @staticmethod
    def get_roles(instance) -> list[int]:
        """返回用户关联的角色 ID 列表"""
        return [role.id for role in instance.role.all()]

    def get_deptName(self, instance) -> str | None:
        """
        返回用户所属部门名称

        用户与部门为多对一关系（User.dept 外键），未分配部门时返回 None，
        由前端决定展示占位或隐藏。
        """
        dept = getattr(instance, "dept", None)
        return dept.name if dept else None

    def get_avatar(self, instance) -> str | None:
        """
        返回用户头像的绝对 URL

        头像为多对一关系（User.avatar 取第一条），通过请求上下文
        将相对路径转换为完整 URL；无头像时返回 None。
        """
        avatar = instance.avatar.first()
        if not avatar:
            return None
        # 通过请求对象构建绝对 URL（相对路径 → 完整路径）
        request = self.context.get("request")
        return request.build_absolute_uri(avatar.path.url)

    def get_accessToken(self, instance) -> str | None:
        """从序列化器上下文获取访问令牌；未注入时返回 None"""
        access_token = self._get_access_token()
        return str(access_token) if access_token else None

    def get_refreshToken(self, instance) -> str | None:
        """从序列化器上下文获取刷新令牌；未注入（如验证接口）时返回 None"""
        refresh_token = self.context.get("refresh_token")
        return str(refresh_token) if refresh_token else None

    def get_expires(self, instance) -> int | None:
        """
        返回访问令牌的过期时间戳（毫秒）

        JWT 的 exp 为标准 Unix 秒级时间戳，转换为毫秒以匹配前端约定；
        未注入访问令牌时返回 None。
        """
        access_token = self._get_access_token()
        if not access_token:
            return None
        return int(access_token.payload["exp"]) * 1000

    def _get_access_token(self):
        """私有辅助方法：获取上下文中注入的访问令牌，供多个方法复用"""
        return self.context.get("access_token")

    class Meta:
        model = User
        fields = [
            "id", "refreshToken", "accessToken", "expires",
            "username", "name", "avatar", "roles", "deptName",
        ]


def get_user_by_login(login_value: str):
    """
    按登录名查找用户，支持用户名 / 邮箱 / 手机号三种方式

    Args:
        login_value: 用户输入的登录名（用户名、邮箱或手机号）

    Returns:
        User | None: 找到的用户实例；不存在时返回 None
    """
    try:
        # 三种字段任一匹配即可（等价于 OR 查询）
        query = Q(username=login_value) | Q(email=login_value) | Q(mobile=login_value)
        return User.objects.get(query)
    except User.DoesNotExist:
        return None
    except User.MultipleObjectsReturned:
        # 边界处理：同一登录值同时命中多个用户（如 A 的 username 等于 B 的 email）时，
        # 优先按用户名精确匹配，避免登录接口 500
        try:
            return User.objects.get(username=login_value)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None


def user_login(user, request) -> dict:
    """
    为用户生成 token 并返回统一序列化的用户信息

    适用于登录、第三方登录、重置密码后自动登录等场景。

    Args:
        user: 已通过认证的用户实例
        request: 当前请求对象（用于构建头像绝对 URL 与发送登录信号）

    Returns:
        dict: 统一用户信息结构（含 accessToken / refreshToken / expires / 用户基础信息）
    """
    # 发送登录信号（simplejwt 依赖该信号维护黑名单与登录审计等）
    user_logged_in.send(sender=user.__class__, request=request, user=user)

    # 生成刷新令牌，并从中派生访问令牌
    refresh_token = RefreshToken.for_user(user)
    access_token = refresh_token.access_token

    # 将 token 注入序列化器上下文，由 UserTokenSerializer 统一格式化输出
    serializer = UserTokenSerializer(
        user,
        context={
            "request": request,
            "refresh_token": refresh_token,
            "access_token": access_token,
        },
    )
    return serializer.data


@extend_schema(tags=["用户登录"])
class CustomTokenObtainPairView(TokenObtainPairView):
    """自定义登录接口：支持用户名 / 邮箱 / 手机号登录，返回统一用户信息"""

    @extend_schema(summary="获取token", extensions={"x-function": "TokenObtainPair"})
    def post(self, request, *args, **kwargs):
        """
        登录接口

        支持通过用户名 / 邮箱 / 手机号登录。
        安全策略：开发环境区分"用户不存在"与"密码错误"便于调试；
        生产环境统一提示"用户名或密码错误"，防止账号枚举。

        Args:
            request: 请求对象，body 需携带 {"username": ..., "password": ...}
        """
        # 提取登录凭据
        login_value = request.data.get("username")
        password = request.data.get("password")

        # 按登录名查找用户（用户名 / 邮箱 / 手机号）
        user = get_user_by_login(login_value)
        if user is None:
            # 开发环境明确提示用户不存在，生产环境模糊提示以增强安全性
            message = "用户名不存在" if settings.DEBUG else "用户名或密码错误"
            return error_response(message=message)

        # 校验密码
        if not user.check_password(password):
            return error_response(message="密码错误")

        # 校验账号状态：未激活账号禁止登录
        if not user.is_active:
            return error_response(message="账户未激活，请联系管理员")

        # 生成 token 并返回统一用户信息
        data = user_login(user, request)
        return success_response(message="登录成功", data=data)


@extend_schema(tags=["用户登录"])
class CustomTokenVerifyView(TokenVerifyView):
    """自定义 token 验证接口：验证访问令牌有效性，返回统一用户信息"""

    @extend_schema(summary="验证token", extensions={"x-function": "TokenVerify"})
    def post(self, request, *args, **kwargs):
        """
        验证 access_token 是否有效

        校验通过后返回与登录接口一致的用户信息（不含 refreshToken）。

        Args:
            request: 请求对象，body 需携带 {"token": ...}
        """
        token_value = request.data.get("token")
        if not token_value:
            return error_response(message="缺少 token")

        try:
            # 解码并验证访问令牌，从载荷中取出用户 ID
            access_token = AccessToken(token_value)
            user = User.objects.get(id=access_token["user_id"])
        except (InvalidToken, TokenError):
            # 令牌无效、签名错误或已过期
            return error_response(message="无效或过期的 token")
        except User.DoesNotExist:
            # 令牌有效但对应用户已被删除
            return error_response(message="用户不存在")

        # 使用统一序列化器返回用户信息（验证接口不注入刷新令牌）
        serializer = UserTokenSerializer(
            user,
            context={
                "request": request,
                "refresh_token": None,
                "access_token": access_token,
            },
        )
        return success_response(message="token 验证成功", data=serializer.data)


@extend_schema(tags=["用户登录"])
class CustomTokenRefreshView(TokenRefreshView):
    """自定义 token 刷新接口：用刷新令牌换取新的访问令牌"""

    @extend_schema(summary="刷新token", extensions={"x-function": "TokenRefresh"})
    def post(self, request, *args, **kwargs):
        """
        刷新 token

        使用有效的 refresh_token 获取新的 access_token：
        - 成功时返回新的 access_token 及用户信息；
        - refresh_token 无效、过期或格式错误时返回错误响应；
        - 建议前端在 access_token 过期前主动刷新。

        Args:
            request: 请求对象，body 需携带 {"refresh": ...}
        """
        refresh_token_value = request.data.get("refresh")
        if not refresh_token_value:
            return error_response(message="需要提供 refresh_token")

        try:
            # 解析刷新令牌，并派生新的访问令牌
            refresh_token = RefreshToken(refresh_token_value)
            access_token = refresh_token.access_token
            if refresh_token.get('oa_sso'):
                # OA 登录的本地令牌不能超过本次 OA 授权截止时间。
                access_token['exp'] = min(access_token['exp'], refresh_token['exp'])

            # 从刷新令牌中提取用户 ID 并加载用户
            user_id = refresh_token.get("user_id")
            if not user_id:
                return error_response(message="refresh_token 中缺少用户信息")
            user = User.objects.get(id=user_id)

            # 使用统一序列化器返回用户信息（刷新令牌原样回传）
            serializer = UserTokenSerializer(
                user,
                context={
                    "request": request,
                    "refresh_token": refresh_token_value,
                    "access_token": access_token,
                },
            )
            return success_response(message="刷新 Token 成功", data=serializer.data)

        except (InvalidToken, TokenError) as exc:
            # 令牌无效、签名错误或已过期
            return error_response(message=f"Refresh token 无效或已过期: {str(exc)}")
        except User.DoesNotExist:
            # 令牌有效但对应用户已被删除
            return error_response(message="用户不存在")
        except Exception as exc:
            # 兜底捕获，避免未处理异常直接抛给前端
            logger.exception("刷新 token 时发生未预期异常")
            return error_response(message=f"刷新失败: {str(exc)}")


class OnlineUserSerializer(serializers.ModelSerializer):
    """在线用户信息序列化器"""
    username = serializers.SerializerMethodField(help_text="用户名")

    @staticmethod
    def get_username(instance) -> str:
        """安全获取用户名，处理 user 为 None 的情况"""
        if instance.user:
            return instance.user.username
        return UNKNOWN_USER_DISPLAY

    class Meta:
        model = OutstandingToken
        fields = ["user_id", "username", "jti", "created_at", "expires_at"]


@extend_schema(tags=["用户登录"])
class CustomTokenOnlineView(GenericAPIView):
    """
    在线用户列表接口

    通过查询 OutstandingToken 表获取所有未过期的 refreshToken 对应会话
    （排除已加入黑名单的 token），并按用户分组展示。
    同一用户的多次登录会合并为一个用户条目，展示其全部会话。

    权限要求：需登录。
    """
    serializer_class = OnlineUserSerializer
    pagination_class = None  # 不使用默认分页，手动处理分组后的分页

    @extend_schema(summary="获取在线用户", extensions={"x-function": "TokenOnline"})
    def get(self, request):
        """获取在线用户列表（按用户分组 + 手动分页）"""
        current_time = timezone.now()

        # 查询所有未过期且关联用户的 token，排除已拉黑的会话，按创建时间倒序
        queryset = (
            OutstandingToken.objects.select_related("user")
            .filter(expires_at__gt=current_time, user__isnull=False)
            .exclude(blacklistedtoken__isnull=False)
            .order_by("-created_at")
        )

        # 按用户 ID 分组：每个用户条目包含基本信息和会话列表
        user_sessions = defaultdict(
            lambda: {"user_id": None, "name": "", "username": "", "sessions": []}
        )

        for token in queryset:
            user_id = token.user_id
            session_entry = user_sessions[user_id]
            # 首次遇到该用户时初始化基本信息
            if session_entry["user_id"] is None:
                session_entry["user_id"] = user_id
                session_entry["username"] = token.user.username if token.user else UNKNOWN_USER_DISPLAY
                session_entry["name"] = token.user.name if token.user else UNKNOWN_USER_DISPLAY

            # 将会话起止时间从 UTC 转为本地时区，并格式化为展示字符串
            created_at_local = timezone.localtime(token.created_at) if token.created_at else None
            expires_at_local = timezone.localtime(token.expires_at) if token.expires_at else None
            session_entry["sessions"].append({
                "jti": token.jti,
                "created_at": created_at_local.strftime(DATETIME_DISPLAY_FORMAT) if created_at_local else None,
                "expires_at": expires_at_local.strftime(DATETIME_DISPLAY_FORMAT) if expires_at_local else None,
            })

        # 分组字典转为列表，并为每个用户补充会话数量字段
        user_list = []
        for user_data in user_sessions.values():
            user_data["session_count"] = len(user_data["sessions"])
            user_list.append(user_data)

        # 统计总用户数与总会话数
        total_users = len(user_list)
        total_sessions = sum(len(item["sessions"]) for item in user_list)

        # 手动分页：从查询参数读取页码与每页条数
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))

        # 计算切片范围并截取当前页数据
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_user_list = user_list[start_index:end_index]

        # 计算总页数（向上取整）
        total_pages = (total_users + limit - 1) // limit if total_users > 0 else 0

        # 构建分页元信息（含上一页 / 下一页链接）
        pagination_info = {
            "page": page,
            "limit": limit,
            "total": total_users,
            "total_pages": total_pages,
            "next": f"?page={page + 1}&limit={limit}" if end_index < total_users else None,
            "previous": f"?page={page - 1}&limit={limit}" if page > 1 and (page - 2) * limit < total_users else None,
        }

        return success_response(
            data=paginated_user_list,
            message=f"获取在线用户列表成功，共 {total_users} 个用户，{total_sessions} 个在线会话",
            paginated=pagination_info,
        )


@extend_schema(tags=["用户登录"])
class CustomTokenBlacklistView(GenericAPIView):
    """
    踢用户下线接口

    将该用户所有未过期的 RefreshToken 加入黑名单（SimpleJWT 默认机制），
    使其无法再刷新 token，从而实现强制下线。

    权限要求：仅管理员(is_staff)或超级管理员(is_superuser)可操作。
    """

    @staticmethod
    def has_permission(request) -> bool:
        """
        自定义权限校验：允许管理员或超级管理员访问

        Args:
            request: 当前请求对象

        Returns:
            bool: 是否为管理员或超级管理员
        """
        return bool(
            request.user and
            (request.user.is_staff or request.user.is_superuser)
        )

    @extend_schema(
        summary="踢用户下线",
        description="将指定用户的所有 refreshToken 加入黑名单，使其无法刷新 token。\n\n**权限要求：管理员(is_staff)或超级管理员(is_superuser)可操作**",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "要踢下线的用户ID",
                        "example": 1,
                    }
                },
                "required": ["user_id"],
            }
        },
        responses={
            "200": OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "success": {
                            "type": "boolean",
                            "description": "操作成功标志",
                            "example": True,
                        },
                        "code": {
                            "type": "integer",
                            "description": "业务状态码",
                        },
                    },
                },
                description="用户下线成功",
            )
        },
        extensions={"x-function": "TokenBlacklist"},
    )
    def post(self, request):
        """
        执行踢用户下线操作

        Args:
            request: 请求对象，body 需携带 {"user_id": ...}

        Returns:
            Response: 统一格式响应，data 含拉黑统计信息
        """
        # 权限校验
        if not self.has_permission(request):
            return error_response(message="权限不足")

        # 参数校验
        user_id = request.data.get("user_id")
        if not user_id:
            return error_response(message="请提供用户ID")

        try:
            # 验证目标用户是否存在
            user = User.objects.get(id=user_id)

            # 查询该用户所有未过期的 refreshToken，按创建时间倒序
            current_time = timezone.now()
            user_tokens = OutstandingToken.objects.filter(
                user=user,
                expires_at__gt=current_time,
            ).order_by("-created_at")

            # 无活跃会话时直接返回
            if not user_tokens.exists():
                return error_response(message="该用户没有活跃的 token")

            # 统计待处理 token 总数（复用计数，避免多次执行 COUNT 查询）
            total_count = user_tokens.count()

            # 逐个拉黑 token：已在黑名单中的跳过，单个失败不影响整体流程
            kicked_count = 0
            failed_count = 0
            for token in user_tokens:
                try:
                    # 幂等处理：已拉黑的 token 不再重复创建
                    if not BlacklistedToken.objects.filter(token=token).exists():
                        BlacklistedToken.objects.create(token=token)
                        kicked_count += 1
                except Exception as exc:
                    # 单个 token 失败不中断整体流程，记录日志后继续
                    logger.warning("拉黑 token %s 失败: %s", token.jti, exc)
                    failed_count += 1

            # 组装操作结果
            result_data = {
                "kicked_tokens": kicked_count,
                "failed_tokens": failed_count,
                "total_tokens": total_count,
                "user_id": user_id,
                "name": user.name,
                "username": user.username,
            }

            # 构建返回提示信息（存在失败项时补充详细统计）
            message = f"成功将用户 {user.username} 踢下线"
            if failed_count > 0:
                message += f"，共处理 {total_count} 个 refreshToken，成功拉黑 {kicked_count} 个，失败 {failed_count} 个"
            else:
                message += f"，共拉黑 {kicked_count} 个 refreshToken"

            return success_response(message=message, data=result_data)

        except User.DoesNotExist:
            # 目标用户不存在
            return error_response(message="用户不存在")
        except Exception as exc:
            # 兜底捕获，避免未处理异常直接抛给前端
            logger.exception("踢用户下线时发生未预期异常")
            return error_response(message=f"踢用户下线失败: {str(exc)}")

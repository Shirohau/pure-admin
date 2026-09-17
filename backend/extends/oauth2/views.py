#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：views.py
@Author  ：李小涛
@Date    ：2025/12/1 下午8:12 
@Explain : OAuth2 第三方登录视图层
"""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import action

from extends.drf.response import error_response, success_response
from extends.drf.views_mixins import CrudViewSet
from .filters import UserOAuthFilter
from .models import UserOAuthModel
from .serializers import UserOAuthSerializer
from .service import OAuthService
from .config import get_platform_config

User = get_user_model()


@extend_schema(tags=["第三方账号"])
class UserOAuthView(CrudViewSet):
    """OAuth2 第三方登录管理视图"""
    queryset = UserOAuthModel.objects.all()
    serializer_class = UserOAuthSerializer
    filterset_class = UserOAuthFilter
    select_related = ['user']  # 默认需要关联的外键表

    @extend_schema(
        summary="获取第三方配置",
        description="获取指定平台的OAuth2配置信息",
        parameters=[
            OpenApiParameter(name='platform', description='平台名称 (weibo/gitee/work_weixin)', required=True,
                             type=str),
            OpenApiParameter(name='kind', description='平台类型 (PC/M)', required=True, type=str),
        ]
    )
    @action(methods=["GET"], detail=False, permission_classes=[])
    def get_config(self, request, *args, **kwargs):
        """
        获取第三方认证配置信息
        
        配置项说明：
        - client_id: 应用ID
        - client_secret: 应用密钥
        - redirect_uri: 回调地址
        - authorize_uri: 授权页面地址
        - token_uri: Token交换地址
        - userinfo_uri: 用户信息查询地址
        """
        platform = request.query_params.get('platform')
        kind = request.query_params.get('kind')

        if not platform or not kind:
            return error_response(message="缺少必要参数: platform, kind")

        try:
            config_dict = get_platform_config(platform, kind)
            return success_response(data=config_dict)
        except ValueError as e:
            return error_response(message=str(e))

    @extend_schema(summary="OAuth2回调处理")
    @action(methods=["POST"], detail=False, permission_classes=[])
    def callback(self, request, *args, **kwargs):
        """
        处理前端跳转回来的 OAuth 回调，支持登录和绑定两种场景
        
        请求体需包含：
        - platform: 平台名称 (weibo/gitee/work_weixin)
        - kind: 平台类型 (PC/M)，用于区分不同 redirect_uri
        - source: 操作类型 (login/binding)
        - code: 授权码
        - user_id: 当前用户ID（仅 binding 时需要）
        """
        # 交由服务层处理
        try:
            service = OAuthService(request)
            return service.handle()
        except ValueError as e:
            return error_response(message=str(e))
        except Exception as e:
            return error_response(message="服务器内部错误，请稍后重试")

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/11/26 上午11:00 
@Explain : drf 配置文件
"""

from application import settings

# ********** 注册APP **********
settings.INSTALLED_APPS += ['rest_framework', 'django_filters']

# ********** 注册中间件 **********
# settings.MIDDLEWARE += []

# ********** 注册路由 **********
settings.PLUGINS_URL_PATTERNS += [{"path": r'api-auth/', "include": "rest_framework.urls"}]

# ********** 注册配置 **********
REST_FRAMEWORK = {
    # ===========================================================================
    # 1. 认证 (Authentication)
    # 控制用户如何被识别身份
    # ===========================================================================
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # JWT 认证
        'rest_framework.authentication.SessionAuthentication',  # 浏览器登录态（开发调试用）
        # 'rest_framework.authentication.TokenAuthentication',        # DRF 默认 Token
        # 'rest_framework.authentication.BasicAuthentication',        # HTTP Basic（不推荐生产使用）
    ],

    # ===========================================================================
    # 2. 权限 (Permissions)
    # 控制认证后的用户是否有权访问资源
    # ===========================================================================
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # 默认需登录
        # 'rest_framework.permissions.AllowAny',               # 允许任何人（慎用）
        # 'rest_framework.permissions.IsAdminUser',            # 仅管理员
        # 'myapp.permissions.CustomPermission',                # 自定义权限
    ],

    # ===========================================================================
    # 3. 解析器 (Parsers)
    # 定义 API 如何解析客户端发送的请求体数据
    # ===========================================================================
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',  # application/json
        'rest_framework.parsers.FormParser',  # application/x-www-form-urlencoded
        'rest_framework.parsers.MultiPartParser',  # multipart/form-data（文件上传）
        # 'rest_framework.parsers.FileUploadParser',      # 大文件流式上传（需配合特定视图）
    ],

    # ===========================================================================
    # 4. 渲染器 (Renderers)
    # 定义 API 返回数据的格式（如 JSON、HTML 可浏览 API）
    # ===========================================================================
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',  # 生产环境建议只保留 JSON
        'rest_framework.renderers.BrowsableAPIRenderer',  # Web 可操作界面（仅开发环境启用）
    ],

    # ===========================================================================
    # 5. 分页 (Pagination)
    # 控制列表接口的分页行为
    # ===========================================================================
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_PAGINATION_CLASS': 'extends.drf.pagination.CustomPageNumberPagination',
    'PAGE_SIZE': 10,  # 默认每页数量（若分页类未覆盖）

    # ===========================================================================
    # 6. 过滤、搜索、排序 (Filtering, Searching, Ordering)
    # 提供灵活的查询能力
    # ===========================================================================
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',  # 标准 django-filter
        'rest_framework.filters.SearchFilter',  # 搜索（?search=关键字）
        'rest_framework.filters.OrderingFilter',  # 排序（?ordering=field,-field）
    ],
    'SEARCH_PARAM': 'search',  # 搜索字段名
    'ORDERING_PARAM': 'ordering',  # 排序字段名

    # ===========================================================================
    # 7. 日期时间格式化 (Date & Time Formatting)
    # 控制序列化时日期时间的输出格式
    # ===========================================================================
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',  # 日期时间格式
    'DATE_FORMAT': '%Y-%m-%d',  # 日期格式
    'TIME_FORMAT': '%H:%M:%S',  # 时间格式
    'COERCE_DECIMAL_TO_STRING': True,  # Decimal 字段转为字符串输出，避免 JS 精度丢失

    # ===========================================================================
    # 8. 异常处理 (Exception Handling)
    # 自定义异常响应结构，统一错误格式
    # ===========================================================================
    # 'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'EXCEPTION_HANDLER': 'extends.drf.response.custom_exception_handler',

    # ===========================================================================
    # 9. 限流 (Throttling)
    # 防止接口被恶意刷请求
    # ===========================================================================
    'DEFAULT_THROTTLE_CLASSES': [
        # 'rest_framework.throttling.AnonRateThrottle',   # 匿名用户限流
        # 'rest_framework.throttling.UserRateThrottle',   # 登录用户限流
        # 'rest_framework.throttling.ScopedRateThrottle', # 视图级别限流
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',  # 匿名用户：每分钟最多60次
        'user': '1000/hour',  # 登录用户：每小时最多1000次
        # 'login': '5/minute',    # 可用于登录接口单独限流
    },

    # ===========================================================================
    # 10. 版本控制 (Versioning)
    # 支持 API 多版本管理
    # ===========================================================================
    # 'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    # 'DEFAULT_VERSION': 'v1',
    # 'ALLOWED_VERSIONS': ['v1', 'v2'],
    # 'VERSION_PARAM': 'version',

    # ===========================================================================
    # 11. 视图默认类 (Default View Class)
    # ===========================================================================
    # 'DEFAULT_VIEW_CLASS': 'rest_framework.views.APIView',

    # ===========================================================================
    # 12. API 文档与可浏览 API 设置
    # ===========================================================================
    'HTML_SELECT_CUTOFF': 1000,  # 下拉框超过1000项显示搜索框
    'HTML_SELECT_CUTOFF_TEXT': '开始搜索...',  # 超出提示文字
    'URL_FORMAT_OVERRIDE': None,  # 禁用 ?format=json 这类参数（安全考虑）
    'STRICT_JSON': True,  # 严格 JSON 模式（非法 JSON 抛错）
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',  # 测试客户端默认使用 JSON
    'TEST_REQUEST_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],

    # ===========================================================================
    # 13. 其他杂项配置
    # ===========================================================================
    'URL_FIELD_NAME': 'url',  # 序列化器中生成的链接字段名
    'NON_FIELD_ERRORS_KEY': 'non_field_errors',  # 非字段错误的 key 名
    'REMOVE_FSLASH_PARAMETERS': False,  # 是否移除 ;param=value 这类参数（旧式）
    'NUM_PROXIES': None,  # 反向代理层数，影响 real_ip 获取

    # ===========================================================================
    # 14. Schema / OpenAPI 配置（用于 drf-spectacular 或 drf-yasg）
    # ===========================================================================
    # 'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',  # 如果使用 drf-spectacular
}

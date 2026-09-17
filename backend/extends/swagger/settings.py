#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：settings.py
@Author  ：李小涛
@Date    ：2025/11/26 上午11:00 
@Explain : api 文档 配置
"""
from application import settings

# ********** 注册路由 **********
settings.PLUGINS_URL_PATTERNS += [{"path": r'', "include": "extends.swagger.urls"}]

# ******** 注册中间件 **********
# settings.MIDDLEWARE += []

# ********** 注册APP **********
settings.INSTALLED_APPS += ['drf_spectacular', 'drf_spectacular_sidecar']

# ******** 修改DRF配置 ********
settings.REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'

# ********** swagger配置 **********
SPECTACULAR_SETTINGS = {
    # ==================== 基础元信息 ====================
    "TITLE": "学习平台 API",
    "DESCRIPTION": (
        "后端接口文档。\n\n"
        "**主要模块**：用户认证、课程管理、订单系统、学习记录。\n\n"
        "> ⚠️ 测试环境数据每周日重置，请勿存储重要数据。"
    ),
    "VERSION": "1.0.0",
    # "TOS": "https://example.com/terms-of-service/",  # 服务条款链接
    #
    # # 联系人与许可证
    # "CONTACT": {
    #     "name": "API 技术支持",
    #     "email": "api-support@example.com",
    #     "url": "https://example.com/support",
    # },
    # "LICENSE": {
    #     "name": "MIT License",
    #     "url": "https://opensource.org/licenses/MIT",
    # },

    # 多服务器地址（Swagger UI 顶部下拉切换）
    "SERVERS": [
        {"url": "http://localhost:8000", "description": "🔵 本地开发"},
        {"url": "https://staging-api.example.com", "description": "🟡 测试环境"},
        {"url": "https://api.example.com", "description": "🟢 生产环境"},
    ],

    # 外部文档链接
    "EXTERNAL_DOCS": {
        "description": "📖 查看完整文档",
        "url": "https://docs.vuedj.com",
    },


    # ==================== Schema 生成控制 ====================
    # 不将 schema 端点本身包含在文档中
    "SERVE_INCLUDE_SCHEMA": False,

    # 请求体与响应体拆分为独立组件，避免循环引用并提高复用率
    "COMPONENT_SPLIT_REQUEST": True,

    # 路径前缀正则：剥离 URL 中的版本前缀，避免 tag 中出现冗余版本号
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+/",

    # 枚举后处理钩子（强烈推荐）：自动合并重复枚举，大幅精简 Schema 体积
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],

    # 排序规则
    "TAGS_SORTER": "alpha",  # Tag 按字母排序
    "OPERATIONS_SORTER": "method",  # 接口按 HTTP 方法排序 (GET > POST > PUT > PATCH > DELETE)

    # OpenAPI 规范版本（部分代码生成工具仅支持 3.0.x）
    "OAS_VERSION": "3.0.3",

    # 排除不需要出现在文档中的第三方 app
    "EXCLUDE_APPS": [
        "django.contrib.admin",
        "django.contrib.auth",  # 如果使用了自定义 User 视图可保留
        "debug_toolbar",
        "silk",
    ],

    # ==================== 认证与安全 ====================
    # 全局默认安全方案（所有接口默认带 🔒，可通过 @extend_schema(security=[]) 局部豁免）
    "SECURITY": [{"BearerAuth": []}],

    # 自定义认证方案定义
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "输入 JWT Access Token，无需添加 Bearer 前缀",
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "用于服务端间调用的 API Key",
            },
        }
    },

    # ==================== Swagger UI 展示配置 ====================
    # 使用 sidecar 离线资源，避免内网/生产环境加载 CDN 失败
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",

    "SWAGGER_UI_SETTINGS": {
        "filter": True,  # 启用顶部搜索过滤框
        "docExpansion": "list",  # 默认展开所有 Tag 分组（接口详情折叠）
        "deepLinking": True,  # 支持 URL 锚点定位到具体接口
        "persistAuthorization": True,  # 刷新页面后保持已输入的 Token
        "displayOperationId": True,  # 显示 operationId（对应 DRF 视图方法名）
        "defaultModelsExpandDepth": -1,  # 底部 Models 区域默认折叠
        "defaultModelExpandDepth": 2,  # 接口参数模型默认展开 2 层
        "displayRequestDuration": True,  # 显示 Try it out 的请求耗时
        "tryItOutEnabled": True,  # 默认开启 Try it out 编辑模式
        "syntaxHighlight.theme": "monokai",  # 代码高亮主题
    },

    # ReDoc 专属配置
    "REDOC_UI_SETTINGS": {
        "hideDownloadButton": False,  # 显示下载 Schema 按钮
        "expandResponses": "200,201",  # 默认展开成功响应
        "pathInMiddlePanel": True,  # 路径显示在中间面板
        "nativeScrollbars": True,  # 使用原生滚动条
    },

    # ==================== 开发与调试 ====================
    # 开发阶段设为 False 以获取详细警告；生产环境建议设为 True 避免启动异常
    "DISABLE_ERRORS_AND_WARNINGS": False,

    # 当 Serializer 缺少类型注解时，是否回退到 string 类型而非报错
    "ENUM_NAME_OVERRIDES": {},  # 手动覆盖枚举命名，解决同名冲突
}

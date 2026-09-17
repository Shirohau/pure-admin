from application import settings


# ********** 注册APP **********
settings.INSTALLED_APPS += ["extends.oauth2"]

# ********** 注册路由 **********
settings.PLUGINS_URL_PATTERNS += [{"path": r'api/', "include": "extends.oauth2.urls"}]

# ********** 配置 **********
settings.AUTO_REGISTER = True  # 是否允许自动注册
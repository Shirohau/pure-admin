from application import settings


# ********** 注册APP **********
settings.INSTALLED_APPS += ["extends.otp"]

# ********** 注册路由 **********
settings.PLUGINS_URL_PATTERNS += [{"path": r'api/', "include": "extends.otp.urls"}]

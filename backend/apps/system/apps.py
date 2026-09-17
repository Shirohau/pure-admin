from django.apps import AppConfig


class SystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.system'

    def ready(self):
        # 注册登录信号
        import apps.system.models.log_login.signals  # noqa: F401

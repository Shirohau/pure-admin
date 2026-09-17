from django.db import models
from apps.system.models import table_prefix


class LogLoginModel(models.Model):
    username = models.CharField(max_length=20, verbose_name="登录用户", db_comment="登录用户")
    ip_address = models.GenericIPAddressField(verbose_name="IP地址", db_comment="IP地址")
    login_time = models.DateTimeField(auto_now_add=True, verbose_name="登录时间", db_comment="登录时间")

    # 直接来自 ua-parser 的字段
    user_agent = models.TextField(verbose_name="完整 User-Agent", db_comment="完整 User-Agent", blank=True)
    browser = models.CharField(verbose_name="浏览器", db_comment="浏览器", max_length=50, blank=True)
    os_info = models.CharField(verbose_name="操作系统", db_comment="操作系统", max_length=100, blank=True)
    device = models.CharField(verbose_name="设备", db_comment="设备", max_length=100, blank=True)

    class Meta:
        db_table = table_prefix + "log_login"
        verbose_name = "登录日志"
        verbose_name_plural = verbose_name
        db_table_comment = verbose_name
        ordering = ['-login_time']

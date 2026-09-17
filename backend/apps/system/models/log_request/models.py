from django.db import models

from apps.system.models import table_prefix


class LogRequestModel(models.Model):
    username = models.CharField(max_length=20, verbose_name="请求用户", db_comment="请求用户")
    ip_address = models.GenericIPAddressField(verbose_name="IP地址", db_comment="IP地址")
    request_time = models.DateTimeField(auto_now_add=True, verbose_name="请求时间", db_comment="请求时间")

    method = models.CharField(max_length=10, verbose_name="请求方法", db_comment="请求方法")
    url = models.URLField(verbose_name="请求地址", db_comment="status_code")
    feedback = models.TextField(verbose_name="请求反馈", db_comment="请求反馈", blank=True, null=True)
    query_params = models.TextField(verbose_name="请求参数", db_comment="请求参数")

    class Meta:
        db_table = table_prefix + "log_request"
        verbose_name = "请求日志"
        verbose_name_plural = verbose_name
        db_table_comment = verbose_name
        ordering = ['-request_time']

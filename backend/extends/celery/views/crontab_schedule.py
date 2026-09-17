"""
@author: 木子李
@contact: QQ:1537080775
@Created on: 2025-03-08
@Remark: 周期触发器
"""

from django_celery_beat.models import CrontabSchedule
from drf_spectacular.utils import extend_schema
from rest_framework import serializers

from extends.drf.views_mixins import CrudViewSet


class CrontabScheduleSerializer(serializers.ModelSerializer):
    """
    周期触发器 查询序列化
    """
    timezone = serializers.SerializerMethodField(help_text="时区")
    human_readable = serializers.SerializerMethodField(help_text="表达式", read_only=True)
    described = serializers.SerializerMethodField(read_only=True)
    cron = serializers.SerializerMethodField(help_text="cron表达式", read_only=True)

    def get_cron(self, instance) -> str:
        return '{} {} {} {} {}'.format(
            instance.minute, instance.hour, instance.day_of_month, instance.month_of_year, instance.day_of_week
        )

    def get_described(self, instance) -> str:
        return instance.__str__()

    def get_human_readable(self, instance) -> str:
        """
       获取 CrontabSchedule 实例的人类可读的时间表达式。

       :param instance: CrontabSchedule 实例
       :return: 人类可读的时间表达式
       """
        return instance.human_readable

    def get_timezone(self, instance) -> str:
        return str(instance.timezone)  # 使用 str() 方法将 ZoneInfo 对象转换为字符串表示

    class Meta:
        model = CrontabSchedule
        fields = '__all__'


@extend_schema(tags=["周期触发器"])
class CrontabScheduleViewSet(CrudViewSet):
    """
    CrontabSchedule 周期触发器
    minute 分钟
    hour 小时
    day_of_week 每周的周几
    day_of_month 每月的某一天
    month_of_year 每年的某一个月

    """
    queryset = CrontabSchedule.objects.all()
    serializer_class = CrontabScheduleSerializer
    ordering = '-id'  # 默认排序
    select_related = []

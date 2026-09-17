"""
@author: 木子李
@contact: QQ:1537080775
@Created on: 2025-03-08
@Remark: 间隔触发器
"""

from django_celery_beat.models import IntervalSchedule
from drf_spectacular.utils import extend_schema
from rest_framework import serializers

from extends.drf.views_mixins import CrudViewSet


class IntervalScheduleSerializer(serializers.ModelSerializer):
    described = serializers.SerializerMethodField(read_only=True)

    def get_described(self, instance) -> str:
        return instance.__str__()

    class Meta:
        model = IntervalSchedule
        fields = '__all__'


@extend_schema(tags=["间隔触发器"])
class IntervalScheduleViewSet(CrudViewSet):
    """
    IntervalSchedule 间隔触发器
    every 次数
    period 时间(天,小时,分钟,秒.毫秒)
    """
    queryset = IntervalSchedule.objects.all()
    serializer_class = IntervalScheduleSerializer
    ordering = '-id'  # 默认排序
    select_related = []

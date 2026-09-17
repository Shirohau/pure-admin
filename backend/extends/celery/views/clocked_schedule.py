"""
@author: 木子李
@contact: QQ:1537080775
@Created on: 2025-03-08
@Remark: 定时触发器
"""

from django_celery_beat.models import ClockedSchedule
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from extends.drf.views_mixins import CrudViewSet


class ClockedScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClockedSchedule
        fields = '__all__'


@extend_schema(tags=["定时触发器"])
class ClockedScheduleViewSet(CrudViewSet):
    """
    ClockedSchedule 定时触发器
    clocked_time 指定时间
    """
    queryset = ClockedSchedule.objects.all()
    serializer_class = ClockedScheduleSerializer
    ordering = '-id'  # 默认排序
    select_related = []

"""
@author: 木子李
@contact: QQ:1537080775
@Created on: 2025-03-08
@Remark: 任务详情
"""
import django_filters
from django_celery_results.models import TaskResult
from drf_spectacular.utils import extend_schema
from rest_framework import serializers

from extends.drf.filters import CustomFilter
from extends.drf.views_mixins import CrudViewSet


class TaskResultFilter(CustomFilter):
    class Meta:
        model = TaskResult
        fields = "__all__"


class TaskResultSerializer(serializers.ModelSerializer):
    """定时任务详情 序列化器"""

    class Meta:
        model = TaskResult
        fields = '__all__'


@extend_schema(tags=["任务详情"])
class TaskResultViewSet(CrudViewSet):
    """
    定时任务详情
    """
    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer
    filterset_class = TaskResultFilter
    search_fields = ("periodic_task_name", "task_name")
    select_related = []

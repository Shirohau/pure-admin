"""
@author: 木子李
@contact: QQ:1537080775
@Created on: 2025-03-08
@Remark: 定时任务
"""

from celery import current_app
from django_celery_beat.models import PeriodicTask
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from extends.drf.response import success_response
from extends.drf.views_mixins import CrudViewSet
from .clocked_schedule import ClockedScheduleSerializer
from .crontab_schedule import CrontabScheduleSerializer
from .interval_schedule import IntervalScheduleSerializer
from ...drf.filters import CustomFilter


class PeriodicTaskFilter(CustomFilter):
    class Meta:
        model = PeriodicTask
        fields = "__all__"


class PeriodicTaskSerializer(serializers.ModelSerializer):
    clocked_obj = ClockedScheduleSerializer(help_text="定时触发器", source="clocked", read_only=True)
    interval_obj = IntervalScheduleSerializer(help_text="间隔触发器", source="interval", read_only=True)
    crontab_obj = CrontabScheduleSerializer(help_text="周期触发器", source="crontab", read_only=True)

    class Meta:
        model = PeriodicTask
        fields = '__all__'


@extend_schema(tags=["定时任务"])
class PeriodicTaskViewSet(CrudViewSet):
    """
    PeriodicTask celery 任务数据模型
    name 名称
    task celery任务名称
    interval 频率
    crontab 任务编排
    args 形式参数
    kwargs 位置参数
    queue 队列名称
    exchange 交换
    routing_key 路由密钥
    expires 过期时间
    enabled 是否开启
    """
    queryset = PeriodicTask.objects.exclude(name="celery.backend_cleanup")
    serializer_class = PeriodicTaskSerializer
    filterset_class = PeriodicTaskFilter
    search_fields = ("name",)
    ordering = '-id'  # 默认排序
    select_related = []

    @extend_schema(summary="任务列表", extensions={'x-function': 'jobList'})
    @action(methods=["GET"], detail=False, permission_classes=[IsAuthenticated])
    def job_list(self, request, *args, **kwargs):
        # 导入当前应用中默认配置的模块
        current_app.loader.import_default_modules()
        # 获取Celery应用实例中的所有任务名称
        all_tasks = current_app.tasks
        # 白名单：只允许列出这些 app 下的任务
        TASK_APP_WHITELIST = ['extends.celery']

        task_list = []
        for task_name, task_func in all_tasks.items():
            # 跳过 celery 内置任务
            if task_name.startswith('celery.'):
                continue

            # 检查任务是否来自白名单中的 app
            # 任务的 __module__ 通常是 'myapp.tasks' 或 'myapp.some.module'
            module_name = getattr(task_func, '__module__', '')
            if not module_name:
                continue

            # 判断 module 是否以白名单中的某个 app 开头
            allowed = any(
                module_name == app or module_name.startswith(f"{app}.")
                for app in TASK_APP_WHITELIST
            )
            if not allowed:
                continue
                # 获取 label：优先 verbose_name，其次 docstring，最后 task_name
            label = (
                    getattr(task_func, 'verbose_name', None)
                    or (task_func.__doc__ and " ".join(task_func.__doc__.split()))
                    or task_name
            )

            task_list.append({"label": label, "value": task_name})
        # 去重（按 task_name）
        seen = set()
        unique_task_list = []
        for item in task_list:
            if item["value"] not in seen:
                unique_task_list.append(item)
                seen.add(item["value"])

        # 排序
        unique_task_list.sort(key=lambda x: x['value'])
        return success_response(message="获取成功", data=unique_task_list)

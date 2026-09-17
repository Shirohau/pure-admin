# -*- coding: utf-8 -*-
from rest_framework import routers
from django.urls import path, include
from .views.clocked_schedule import ClockedScheduleViewSet
from .views.interval_schedule import IntervalScheduleViewSet
from .views.crontab_schedule import CrontabScheduleViewSet
from .views.periodic_task import PeriodicTaskViewSet
from .views.task_result import TaskResultViewSet

router = routers.SimpleRouter()
# 调度间隔
router.register('clocked_schedule', ClockedScheduleViewSet)
router.register('crontab_schedule', CrontabScheduleViewSet)
router.register('interval_schedule', IntervalScheduleViewSet)
router.register('periodic_task', PeriodicTaskViewSet)
router.register('task_result', TaskResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

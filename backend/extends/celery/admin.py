from django.contrib import admin
from django_celery_beat.models import PeriodicTask
from django_celery_beat.admin import PeriodicTaskAdmin as BasePeriodicTaskAdmin


class PeriodicTaskAdmin(BasePeriodicTaskAdmin):
    date_hierarchy = None  # 👈 关键：关闭时间层级（原为 'start_time'）


# 替换原注册
admin.site.unregister(PeriodicTask)
admin.site.register(PeriodicTask, PeriodicTaskAdmin)

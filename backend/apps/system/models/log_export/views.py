import django_filters
from django.utils.module_loading import import_string
from drf_spectacular.utils import extend_schema
from import_export.resources import ModelResource
from import_export_extensions.models import ExportJob
from rest_framework import serializers

from extends.drf.views_mixins import *
from extends.drf.filters import CustomFilter


def resolver_resource_path(resource_path: str) -> str:
    """
    根据 resource_path 获取对应模型的 verbose_name。

    Args:
        resource_path (str): 如 'apps.example.models.publisher.resources.PublisherExportResource'

    Returns:
        str: 模型的 verbose_name，若失败则返回友好提示。
    """
    if not resource_path:
        return ""

    try:
        ResourceClass = import_string(resource_path)
        if not issubclass(ResourceClass, ModelResource):
            return "（非模型资源）"

        # 实例化以获取 _meta（import_export 的标准做法）
        resource_instance = ResourceClass()
        model_class = resource_instance._meta.model
        return str(model_class._meta.verbose_name)

    except (ImportError, AttributeError, TypeError, ValueError):
        return "（无法解析模型）"


class ExportJobFilter(CustomFilter):
    model_verbose_name = django_filters.CharFilter(
        method='filter_model_verbose_name',
        label='导出模型名称',
    )

    def filter_model_verbose_name(self, queryset, name, value):
        """
        根据 model_verbose_name 进行模糊筛选。

        由于 model_verbose_name 并非数据库字段，而是通过 resource_path
        动态解析出的模型 verbose_name，因此需要先获取所有不重复的
        resource_path，解析其 verbose_name，再筛选匹配的记录。
        """
        if not value:
            return queryset

        resource_paths = (
            queryset
            .values_list('resource_path', flat=True)
            .distinct()
        )

        matching_paths = [
            path for path in resource_paths
            if path and value in resolver_resource_path(path)
        ]

        return queryset.filter(resource_path__in=matching_paths)

    class Meta:
        model = ExportJob
        fields = ["export_status"]


class ExportJobSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.name", read_only=True, label="创建人")
    model_verbose_name = serializers.SerializerMethodField(label="导出模型名称")

    def get_model_verbose_name(self, obj) -> str:
        """
        根据 obj.resource_path 动态获取关联模型的 verbose_name
        """
        return resolver_resource_path(obj.resource_path)

    class Meta:
        model = ExportJob
        fields = (
            "id",
            "model_verbose_name",
            "export_status",
            "data_file",
            "progress",
            "export_started",
            "export_finished",
            "created",
            "modified",
            "error_message",
            "created_by"
        )


@extend_schema(tags=["导出日志"])
class ExportJobViewSet(CrudViewSet):
    queryset = (
        ExportJob.objects
        .select_related("created_by")
        .all().order_by("-id")
    )
    serializer_class = ExportJobSerializer
    filterset_class = ExportJobFilter
    http_method_names = ['get']
    select_related = []  # 默认需要关联的外键表

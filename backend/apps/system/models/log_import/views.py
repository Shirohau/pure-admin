import django_filters
from drf_spectacular.utils import extend_schema
from import_export_extensions.api import ImportJobSerializer
from import_export_extensions.models import ImportJob
from rest_framework import serializers

from apps.system.models.log_export.views import resolver_resource_path
from extends.drf.views_mixins import *
from extends.drf.filters import CustomFilter


class ImportJobFilter(CustomFilter):
    model_verbose_name = django_filters.CharFilter(
        method='filter_model_verbose_name',
        label='导入模型名称',
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
        model = ImportJob
        fields = ["import_status"]


class LogImportJobSerializer(ImportJobSerializer):
    created_by = serializers.CharField(source="created_by.name", read_only=True, label="创建人")
    model_verbose_name = serializers.SerializerMethodField(label="导出模型名称")

    def get_model_verbose_name(self, obj) -> str:
        """
        根据 obj.resource_path 动态获取关联模型的 verbose_name
        """
        return resolver_resource_path(obj.resource_path)

    class Meta:
        model = ImportJob
        fields = (
            "id",
            "model_verbose_name",
            "progress",
            "import_status",
            "import_params",
            # "totals",
            "parse_error",
            # "input_error",
            # "skipped_errors",
            "is_all_rows_shown",
            # "importing_data",
            "input_errors_file",
            "import_started",
            "import_finished",
            "force_import",
            "created",
            "modified",
            "error_message",
            "created_by"
        )


@extend_schema(tags=["导入日志"])
class ExportJobViewSet(CrudViewSet):
    queryset = (
        ImportJob.objects
        .all().order_by("-id")
    )
    serializer_class = LogImportJobSerializer
    filterset_class = ImportJobFilter
    # search_fields = ["name", "code"]
    http_method_names = ['get']
    select_related = []  # 默认需要关联的外键表

    def get_queryset(self):
        """优化查询:预加载 created_by 避免 N+1 问题"""
        queryset = super().get_queryset()
        # 注意:必须在父类 get_queryset() 之后调用 select_related
        # 因为父类会过滤 resource_path,我们需要在那个基础上优化
        queryset = queryset.select_related("created_by")
        return queryset

from drf_spectacular.utils import extend_schema

from extends.drf.views_mixins import *

from .filters import LogLoginFilter
from .models import LogLoginModel
from .resources import LogLoginResource
from .serializers import LogLoginSerializer, LogLoginCreateSerializer, LogLoginUpdateSerializer


@extend_schema(tags=["登录日志"])
class LogLoginViewSet(CrudViewSet, ExportMixin, ImportMixin):
    queryset = LogLoginModel.objects.all()
    serializer_class = LogLoginSerializer
    create_serializer_class = LogLoginCreateSerializer
    update_serializer_class = LogLoginUpdateSerializer
    filterset_class = LogLoginFilter
    export_resource_class = LogLoginResource
    import_resource_class = LogLoginResource
    search_fields = ["ip_address", "username"]
    http_method_names = ['get']
    select_related = []  # 默认需要关联的外键表


@extend_schema(tags=["登录日志"])
class LogLoginExportJobViewSet(CustomExportJobViewSet):
    resource_class = LogLoginResource


@extend_schema(tags=["登录日志"])
class LogLoginImportJobViewSet(CustomImportJobViewSet):
    resource_class = LogLoginResource

from drf_spectacular.utils import extend_schema

from extends.drf.views_mixins import *

from .filters import LogRequestFilter
from .models import LogRequestModel
from .resources import LogRequestResource
from .serializers import LogRequestSerializer, LogRequestCreateSerializer, LogRequestUpdateSerializer


@extend_schema(tags=["请求日志"])
class LogRequestViewSet(CrudViewSet, ExportMixin, ImportMixin):
    queryset = LogRequestModel.objects.all()
    serializer_class = LogRequestSerializer
    create_serializer_class = LogRequestCreateSerializer
    update_serializer_class = LogRequestUpdateSerializer
    filterset_class = LogRequestFilter
    export_resource_class = LogRequestResource
    import_resource_class = LogRequestResource
    search_fields = ["username", "ip_address", "url"]
    http_method_names = ['get']
    select_related = []  # 默认需要关联的外键表


@extend_schema(tags=["请求日志"])
class LogRequestExportJobViewSet(CustomExportJobViewSet):
    resource_class = LogRequestResource


@extend_schema(tags=["请求日志"])
class LogRequestImportJobViewSet(CustomImportJobViewSet):
    resource_class = LogRequestResource

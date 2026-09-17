from drf_spectacular.utils import extend_schema

from extends.drf.views_mixins import *

from .filters import ApiWhiteFilter
from .models import ApiWhiteModel
from .resources import ApiWhiteResource
from .serializers import ApiWhiteSerializer, ApiWhiteCreateSerializer, ApiWhiteUpdateSerializer


@extend_schema(tags=["接口白名单"])
class ApiWhiteViewSet(CrudViewSet, ExportMixin, ImportMixin):
    queryset = ApiWhiteModel.objects.all()
    serializer_class = ApiWhiteSerializer
    create_serializer_class = ApiWhiteCreateSerializer
    update_serializer_class = ApiWhiteUpdateSerializer
    filterset_class = ApiWhiteFilter
    export_resource_class = ApiWhiteResource
    import_resource_class = ApiWhiteResource
    search_fields = ["name", "api"]


@extend_schema(tags=["接口白名单"])
class ApiWhiteExportJobViewSet(CustomExportJobViewSet):
    resource_class = ApiWhiteResource


@extend_schema(tags=["接口白名单"])
class ApiWhiteImportJobViewSet(CustomImportJobViewSet):
    resource_class = ApiWhiteResource

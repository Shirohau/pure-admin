from drf_spectacular.utils import extend_schema
from extends.drf.views_mixins import CrudViewSet
from .filters import FileFilter
from .models import FileModel
from .resources import FileResource
from .serializers import FileSerializer


@extend_schema(tags=["附件"])
class FileViewSet(CrudViewSet):
    queryset = FileModel.objects.all()
    serializer_class = FileSerializer
    filterset_class = FileFilter
    export_resource_class = FileResource
    import_resource_class = FileResource
    http_method_names = ['get', 'post', 'delete']
    search_fields = ["name", ]

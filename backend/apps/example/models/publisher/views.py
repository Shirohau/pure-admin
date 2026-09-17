from decimal import Decimal

from django.db.models import Count, Avg
from django.db.models.functions import Coalesce, Round
from drf_spectacular.utils import extend_schema

from extends.drf.views_mixins import *

from .filters import PublisherFilter
from .models import PublisherModel
from .resources import PublisherResource
from .serializers import PublisherSerializer, PublisherCreateSerializer, PublisherUpdateSerializer


@extend_schema(tags=["出版社"])
class PublisherViewSet(CrudViewSet, HistoryMixin, BatchDestroyMixin, ExportMixin, ImportMixin):
    queryset = (
        PublisherModel.objects.all()
        .prefetch_related('book', 'book__updater')
        .annotate(
            book_count=Count('book'),
            avg_price=Coalesce(Round(Avg('book__price'), 2), Decimal(0.00))
        )
        .order_by('-id')
    )
    serializer_class = PublisherSerializer
    create_serializer_class = PublisherCreateSerializer
    update_serializer_class = PublisherUpdateSerializer
    filterset_class = PublisherFilter
    export_resource_class = PublisherResource
    import_resource_class = PublisherResource
    search_fields = ["province", "city", "district"]


@extend_schema(tags=["出版社"])
class PublisherExportJobViewSet(CustomExportJobViewSet):
    resource_class = PublisherResource


@extend_schema(tags=["出版社"])
class PublisherImportJobViewSet(CustomImportJobViewSet):
    resource_class = PublisherResource

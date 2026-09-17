from decimal import Decimal

from django.db.models import Count, Avg
from django.db.models.functions import Coalesce, Round
from drf_spectacular.utils import extend_schema
from extends.drf.views_mixins import *

from .filters import AuthorFilter
from .models import AuthorModel
from .resources import AuthorResource
from .serializers import AuthorSerializer, AuthorCreateSerializer, AuthorUpdateSerializer


@extend_schema(tags=["作者"])
class AuthorViewSet(CrudViewSet, ExportMixin, ImportMixin, HistoryMixin, BatchDestroyMixin):
    queryset = (
        AuthorModel.objects.all()
        .prefetch_related("book", "book__updater")
        .annotate(
            book_count=Count('book'),
            avg_price=Coalesce(Round(Avg('book__price'), 2), Decimal(0.00))
        )
        .order_by('-id')
    )
    serializer_class = AuthorSerializer
    create_serializer_class = AuthorCreateSerializer
    update_serializer_class = AuthorUpdateSerializer
    filterset_class = AuthorFilter
    export_resource_class = AuthorResource
    import_resource_class = AuthorResource
    search_fields = ["name", "biography"]


@extend_schema(tags=["作者"])
class AuthorExportJobViewSet(CustomExportJobViewSet):
    resource_class = AuthorResource


@extend_schema(tags=["作者"])
class AuthorImportJobViewSet(CustomImportJobViewSet):
    resource_class = AuthorResource

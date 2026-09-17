from drf_spectacular.utils import extend_schema

from extends.drf.views_mixins import *
from extends.drf.response import success_response

from .filters import DictionaryFilter
from .models import DictionaryModel
from .resources import DictionaryResource
from .serializers import (
    DictionarySerializer,
    DictionaryCreateSerializer,
    DictionaryUpdateSerializer,
    DictionaryTreeSerializer,
)


@extend_schema(tags=["字典表"])
class DictionaryViewSet(CrudViewSet, ExportMixin, ImportMixin, BatchDestroySortMixin, MoveMixin):
    queryset = DictionaryModel.objects.all()
    serializer_class = DictionarySerializer
    create_serializer_class = DictionaryCreateSerializer
    update_serializer_class = DictionaryUpdateSerializer
    filterset_class = DictionaryFilter
    export_resource_class = DictionaryResource
    import_resource_class = DictionaryResource
    extra_filter_class = []
    search_fields = ["label", "value"]

    @extend_schema(summary="列表", extensions={"x-function": "List"})
    def list(self, request, *args, **kwargs):
        parent_value = request.query_params.get("parent_value")

        if parent_value and request.query_params.get("status") == "true":
            parent = DictionaryModel.objects.filter(value=parent_value).first()
            if not parent:
                return success_response(message="查询成功", data=[])

            all_items = DictionaryModel.objects.filter(
                level__gt=parent.level,
                status=True
            ).order_by("level", "sort")

            items_dict = {item.id: item for item in all_items}
            for item in all_items:
                item._prefetched_children = []

            for item in all_items:
                if item.parent_id and item.parent_id in items_dict:
                    items_dict[item.parent_id]._prefetched_children.append(item)

            root_children = [item for item in all_items if item.parent_id == parent.id]
            serializer = DictionaryTreeSerializer(
                root_children,
                many=True,
                context={'request': request}
            )
            return success_response(message="查询成功", data=serializer.data)

        return super().list(request, *args, **kwargs)


@extend_schema(tags=["字典表"])
class DictionaryExportJobViewSet(CustomExportJobViewSet):
    resource_class = DictionaryResource


@extend_schema(tags=["字典表"])
class DictionaryImportJobViewSet(CustomImportJobViewSet):
    resource_class = DictionaryResource

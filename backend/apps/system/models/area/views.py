from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import success_response
from extends.drf.views_mixins import *

from .filters import AreaFilter
from .models import AreaModel
from .resources import AreaExportResource, AreaImportResource
from .serializers import AreaSerializer, AreaCreateSerializer, AreaUpdateSerializer


@extend_schema(tags=["地区管理"])
class AreaViewSet(CrudViewSet, ExportMixin, ImportMixin):
    queryset = AreaModel.objects.all()
    serializer_class = AreaSerializer
    create_serializer_class = AreaCreateSerializer
    update_serializer_class = AreaUpdateSerializer
    filterset_class = AreaFilter
    export_resource_class = AreaExportResource
    import_resource_class = AreaImportResource
    search_fields = ["code", "name", "pinyin", "initials"]
    extra_filter_class = []

    @extend_schema(summary="树形数据", extensions={'x-function': 'GetTree'})
    @action(methods=['get'], detail=False)
    def get_tree(self, request, *args, **kwargs):
        max_level = request.query_params.get('max_level', 4)
        # 一次性获取所有启用的地区，并按 code 排序（确保父子顺序）
        areas = list(
            AreaModel.objects.select_related("parent").filter(enable=True, level__lte=max_level)
            .values('code', 'name', 'level', 'parent__code')
            .order_by('code')
        )

        # 构建 code -> node 映射
        node_map = {}
        for item in areas:
            node_map[item['code']] = {
                "code": item['code'],
                "name": item['name'],
                "level": item['level'],
                "children": []
            }
        # 构建树
        tree = []
        for item in areas:
            node = node_map[item['code']]
            parent_code = item['parent__code']
            if parent_code and parent_code in node_map:
                node_map[parent_code]['children'].append(node)
            else:
                # 顶级节点（如省份）
                tree.append(node)
        return success_response(message="查询成功", data=tree)


@extend_schema(tags=["地区管理"])
class AreaExportJobViewSet(CustomExportJobViewSet):
    resource_class = AreaExportResource


@extend_schema(tags=["地区管理"])
class AreaImportJobViewSet(CustomImportJobViewSet):
    resource_class = AreaImportResource

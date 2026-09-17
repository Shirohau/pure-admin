from django.db import transaction
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import error_response, success_response
from extends.drf.views_mixins import *

from .filters import MenuButtonFilter
from .models import MenuButtonModel
from .resources import MenuButtonResource
from .serializers import MenuButtonSerializer, MenuButtonCreateSerializer, MenuButtonUpdateSerializer
from ..menu.models import MenuModel

# 全局缓存 OpenAPI schema，只生成一次
_CACHED_SCHEMA = None

"""
# 注意：需确保视图中设置了扩展
- x-function:权限名字
    @extend_schema(summary="批量新增", extensions={'x-function': 'BatchCreate'})
- x-assign_permission：是否需要设置权限
    extensions={"x-function": "ExportCancel", "x-assign_permission": False},
"""


def get_cached_schema():
    """获取缓存的 OpenAPI schema，首次调用时生成"""
    global _CACHED_SCHEMA
    if _CACHED_SCHEMA is None:
        generator = SchemaGenerator()
        _CACHED_SCHEMA = generator.get_schema(public=True)  # 忽略权限控制
    return _CACHED_SCHEMA


def get_api_list(search: str | None = None, exact: bool = False):
    """
    获取所有 API 接口信息，支持在 tags、path 和 summary 中搜索

    Args:
        search (str | None): 可选，用于在 tags、path 和 summary 中搜索的关键词
        exact (bool): 是否精确匹配，默认为模糊匹配（不区分大小写）

    Returns:
        list: 包含匹配的API接口信息的列表，每个元素为包含以下键的字典：
            - path (str): API路径
            - function (str): 定义的函数名称（来自 x-function 扩展）
            - method (int): HTTP方法对应的排序ID（来自 METHOD_CHOICES）
            - method_des (str): HTTP方法名称（大写，如 'GET'）
            - summary (str): API摘要信息
            - description (str): API详细描述
            - is_secure (bool): 是否需要安全认证（基于 security 字段）
            - id (str): operationId
            - tags (str): 逗号分隔的标签字符串
    """
    schema = get_cached_schema()
    result = []

    # 预处理搜索词
    search_clean = search.strip() if search else None
    search_lower = search_clean.lower() if search_clean else None

    for path, methods in schema.get('paths', {}).items():
        for method, op in methods.items():

            if method.upper() == 'OPTIONS':
                continue

            summary = op.get('summary') or ''
            description = op.get('description') or ''
            tags = op.get('tags') or []
            method_des = method.upper()

            # 搜索匹配逻辑
            matched = True
            if search_lower is not None:
                if exact:
                    # 精确匹配（大小写敏感）
                    matched = search_clean in tags
                else:  # fuzzy
                    # 模糊匹配（不区分大小写）
                    path_match = search_lower in path.lower()
                    summary_match = search_lower in summary.lower()
                    tags_match = any(search_lower in tag.lower() for tag in tags)
                    matched = (path_match or summary_match or tags_match)

            if not matched:
                continue  # 不匹配则跳过

            assign_permission = op.get('x-assign_permission', True)
            if not assign_permission:
                continue  # 不需要权限则跳过

            # 构造结果项
            result.append({
                "tags": ','.join(tags),
                'path': path,
                'function': op.get('x-function'),  # 注意：需确保视图中设置了该扩展
                'method': method_des,  # str: 如 'GET'
                'summary': summary,
                'description': description,
                'is_secure': bool(op.get('security')),
                'id': op.get('operationId', ''),
            })
    return result


@extend_schema(tags=["菜单按钮"])
class MenuButtonViewSet(CrudViewSet, BatchDestroyMixin, MoveMixin):
    queryset = MenuButtonModel.objects.all()
    serializer_class = MenuButtonSerializer
    create_serializer_class = MenuButtonCreateSerializer
    update_serializer_class = MenuButtonUpdateSerializer
    filterset_class = MenuButtonFilter

    @extend_schema(summary="批量新增", extensions={'x-function': 'BatchCreate'})
    @action(methods=["POST"], detail=False)
    @transaction.atomic
    def batch_create(self, request, *args, **kwargs):
        """
        根据菜单ID，批量新增菜单按钮（从后端接口列表中自动匹配）。
        """
        menu_id = request.data.get("menu_id")
        search = request.data.get('search')
        if not menu_id:
            return error_response(message="参数错误：menu_id 为必传参数")
        # 查找菜单（不存在时返回友好错误，避免 500）
        try:
            menu_obj = MenuModel.objects.get(id=menu_id)
        except MenuModel.DoesNotExist:
            return error_response(message=f"菜单不存在：id={menu_id}")
        api_list = get_api_list(search, exact=True)
        # 批量创建 MenuButtonModel
        menu_button_instances = [
            MenuButtonModel(
                menu=menu_obj,
                button_type="api",
                name=api['summary'],
                key=f'{menu_obj.name}:{api["function"]}',
                api=api["path"],
                method=api["method"]
            )
            for api in api_list
        ]
        try:
            # 逐个 save，确保触发 save() 和信号，更新排序 sort 字段
            for instance in menu_button_instances:
                instance.save()
        except Exception as e:
            return error_response(message="批量创建失败", data=str(e))
        return success_response(message="批量创建成功")

    @extend_schema(summary="获取API接口", extensions={'x-function': 'ApiList'})
    @action(methods=["GET"], detail=False)
    def api_list(self, request, *args, **kwargs):
        """
        获取后端所有的API接口
        """
        search = request.query_params.get('search')
        routes = get_api_list(search)
        paginated = {
            "page": 1,
            "limit": len(routes),
            "total": len(routes),
        }
        return success_response(message="获取API列表成功", data=routes, paginated=paginated)


@extend_schema(tags=["菜单按钮"])
class MenuButtonExportJobViewSet(CustomExportJobViewSet):
    resource_class = MenuButtonResource


@extend_schema(tags=["菜单按钮"])
class MenuButtonImportJobViewSet(CustomImportJobViewSet):
    resource_class = MenuButtonResource

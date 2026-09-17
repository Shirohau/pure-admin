from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import success_response, error_response
from extends.drf.utils.models_utils import get_app_model_fields, get_app_models
from extends.drf.views_mixins import *

from .filters import MenuFieldFilter
from .models import MenuFieldModel
from .resources import MenuFieldResource
from .serializers import MenuFieldSerializer, MenuFieldCreateSerializer, MenuFieldUpdateSerializer
from ..menu.models import MenuModel


@extend_schema(tags=["菜单字段"])
class MenuFieldViewSet(CrudViewSet, BatchDestroyMixin):
    """菜单字段视图：管理菜单下的模型字段，并提供模型表/字段的自动匹配辅助接口。"""
    queryset = MenuFieldModel.objects.all().prefetch_related('role_menu_field__role')
    serializer_class = MenuFieldSerializer
    create_serializer_class = MenuFieldCreateSerializer
    update_serializer_class = MenuFieldUpdateSerializer
    filterset_class = MenuFieldFilter

    @extend_schema(summary="批量新增", extensions={'x-function': 'BatchCreate'})
    @action(methods=["POST"], detail=False)
    @transaction.atomic
    def batch_create(self, request, *args, **kwargs):
        """
        根据菜单ID，批量新增菜单字段（自动匹配模型表的全部字段）。
        """
        # 获取参数
        app_model = request.data.get("app_model")
        menu_id = request.data.get("menu_id")
        if not app_model or not menu_id:
            return error_response(message="参数错误：app_model 与 menu_id 为必传参数")
        # 查找菜单（不存在时返回友好错误，避免 500）
        try:
            menu_obj = MenuModel.objects.get(id=menu_id)
        except MenuModel.DoesNotExist:
            return error_response(message=f"菜单不存在：id={menu_id}")
        # 获取模型字段
        app_model_fields = get_app_model_fields(app_model)

        # 批量创建 MenuFieldModel
        menu_field_instances = [
            MenuFieldModel(
                menu=menu_obj,
                model=app_model,
                field_name=info["field_name"],
                verbose_name=info["verbose_name"],
            )
            for info in app_model_fields
        ]
        try:
            MenuFieldModel.objects.bulk_create(menu_field_instances)
        except Exception as e:
            return error_response(message="批量创建失败", data=str(e))
        return success_response(message="批量创建成功")

    @extend_schema(summary="获取模型表", extensions={'x-function': 'AppModels'})
    @action(methods=["GET"], detail=False)
    def app_models(self, request, *args, **kwargs):
        """
        获取所有注册App的模型（供“自动匹配模型表”弹窗选择）。
        """
        search = request.query_params.get('search')
        app_models = get_app_models(search)
        paginated = {
            "page": 1,
            "limit": len(app_models),
            "total": len(app_models),
        }
        return success_response(message="模型表获取成功", data=app_models, paginated=paginated)

    @extend_schema(summary="获取表字段", extensions={'x-function': 'AppModelFields'})
    @action(methods=["GET"], detail=False)
    def app_model_fields(self, request, *args, **kwargs):
        """
        获取指定模型表的字段信息（供新增/编辑表单的“字段显示名”下拉联动）。
        """
        model = request.query_params.get("model")
        app_model_fields = get_app_model_fields(model)
        paginated = {
            "page": 1,
            "limit": len(app_model_fields),
            "total": len(app_model_fields),
        }
        return success_response(message="模型字段获取成功", data=app_model_fields, paginated=paginated)


@extend_schema(tags=["菜单字段"])
class MenuFieldExportJobViewSet(CustomExportJobViewSet):
    resource_class = MenuFieldResource


@extend_schema(tags=["菜单字段"])
class MenuFieldImportJobViewSet(CustomImportJobViewSet):
    resource_class = MenuFieldResource

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import success_response
from extends.drf.views_mixins import *
from .filters import ConfigFilter

from .models import ConfigModel
from .serializers import ConfigSerializer, ConfigCreateSerializer, ConfigUpdateSerializer


@extend_schema(tags=["系统配置表"])
class ConfigViewSet(CrudViewSet):
    queryset = ConfigModel.objects.all()
    serializer_class = ConfigSerializer
    create_serializer_class = ConfigCreateSerializer
    update_serializer_class = ConfigUpdateSerializer
    filterset_class = ConfigFilter

    @extend_schema(summary="获取配置", extensions={'x-function': 'GetConfig'})
    @action(methods=["GET"], detail=False, permission_classes=[], authentication_classes=[])
    def get_config(self, request):
        """
        获取配置文件，不需要登录
        """
        self.extra_filter_class = []
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(message="获取配置文件成功", data=serializer.data)

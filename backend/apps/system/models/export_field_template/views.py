from django.db import IntegrityError, transaction
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError

from extends.drf.views_mixins import CrudViewSet
from .models import ExportFieldTemplateModel
from .serializers import ExportFieldTemplateSerializer


@extend_schema(tags=["导出字段模板"])
class ExportFieldTemplateViewSet(CrudViewSet):
    queryset = ExportFieldTemplateModel.objects.all()
    serializer_class = ExportFieldTemplateSerializer
    extra_filter_class = []
    search_fields = ["name"]

    def get_queryset(self):
        queryset = super().get_queryset().filter(creator=self.request.user)
        api_path = self.request.query_params.get("api_path")
        if api_path:
            queryset = queryset.filter(api_path=api_path)
        return queryset

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(
                    creator=self.request.user,
                    updater=self.request.user,
                    dept_belong_id=self.request.user.dept_id,
                )
        except IntegrityError as exc:
            raise ValidationError({"name": "该业务下已存在同名模板"}) from exc

    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(updater=self.request.user)
        except IntegrityError as exc:
            raise ValidationError({"name": "该业务下已存在同名模板"}) from exc

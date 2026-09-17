from django.db import models

from apps.system.models import table_prefix
from extends.drf.models import CustomModel


class ExportFieldTemplateModel(CustomModel):
    name = models.CharField(max_length=50, verbose_name="模板名称", db_comment="模板名称")
    api_path = models.CharField(max_length=255, verbose_name="业务接口", db_comment="业务接口")
    fields = models.JSONField(default=list, verbose_name="导出字段", db_comment="导出字段")

    class Meta:
        db_table = table_prefix + "export_field_template"
        verbose_name = "导出字段模板"
        verbose_name_plural = verbose_name
        ordering = ("-update_dt", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("creator", "api_path", "name"),
                name="unique_user_export_template_name",
            )
        ]

    def __str__(self):
        return self.name

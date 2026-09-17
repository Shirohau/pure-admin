from rest_framework import serializers

from extends.drf.serializers import CustomSerializer
from .models import ExportFieldTemplateModel


class ExportFieldTemplateSerializer(CustomSerializer):
    skip_field_permissions = True

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("模板名称不能为空")
        return value

    def validate_api_path(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("业务接口不能为空")
        return value

    def validate_fields(self, value):
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("请至少选择一个导出字段")
        if any(not isinstance(item, str) or not item.strip() for item in value):
            raise serializers.ValidationError("导出字段必须是非空字符串数组")
        return list(dict.fromkeys(item.strip() for item in value))

    class Meta:
        model = ExportFieldTemplateModel
        fields = ("id", "name", "api_path", "fields", "create_dt", "update_dt")
        read_only_fields = ("id", "create_dt", "update_dt")

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from rest_framework import serializers

from extends.drf.serializers import CustomSerializer
from .models import ConfigModel
from ..file.models import FileModel


class ConfigSerializer(CustomSerializer):
    skip_field_permissions = True

    class Meta:
        model = ConfigModel
        fields = '__all__'


def _bind_image(instance, file_id):
    """将指定文件绑定到对象"""
    try:
        file_obj = FileModel.objects.select_for_update().get(id=file_id)
    except FileModel.DoesNotExist:
        raise serializers.ValidationError({'file_id': '指定的文件不存在'})

    content_type = ContentType.objects.get_for_model(ConfigModel)
    file_obj.content_type = content_type
    file_obj.object_id = instance.id
    file_obj.save(update_fields=['content_type', 'object_id'])


class ConfigCreateSerializer(CustomSerializer):
    image_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    def create(self, validated_data):
        image_id = validated_data.pop('image_id', None)

        with transaction.atomic():
            instance = super().create(validated_data)
            instance.save()

            # 创建时：如果有 image_id，就绑定
            if image_id is not None and image_id > 0:
                _bind_image(instance, image_id)

        return instance

    class Meta:
        model = ConfigModel
        fields = '__all__'


class ConfigUpdateSerializer(CustomSerializer):
    image_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    def update(self, instance, validated_data):
        image_id = validated_data.pop('image_id', None)

        with transaction.atomic():
            instance = super().update(instance, validated_data)

            # 更新时：仅当显式传了有效 image_id 才绑定
            if 'image_id' in self.initial_data:
                if image_id is not None and image_id > 0:
                    _bind_image(instance, image_id)
                # 否则（如传了非正数或未传）—— 什么也不做，保留原头像

        return instance

    class Meta:
        model = ConfigModel
        fields = '__all__'

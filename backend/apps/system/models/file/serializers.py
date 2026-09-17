import hashlib
import os

from rest_framework import serializers

from extends.drf.serializers import CustomSerializer
from .models import FileModel


def human_readable_size(size_bytes):
    """将字节数转换为人类可读格式，如 1.2 MB"""
    if size_bytes is None or size_bytes == '':
        return "0 B"
    try:
        size = int(size_bytes)
    except (ValueError, TypeError):
        return "0 B"

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


class FileSerializer(CustomSerializer):
    """
    上传文件（不绑定业务对象）
    支持传 folder 字段指定子目录
    """
    file = serializers.FileField(write_only=True, source='path')
    folder = serializers.CharField(max_length=200, required=False, write_only=True)

    size = serializers.SerializerMethodField()
    related_content_type = serializers.SerializerMethodField()
    related_object = serializers.SerializerMethodField()

    file_path = serializers.SerializerMethodField(help_text="简历地址")


    def get_file_path(self, instance) -> str | None:
        if instance.path:
            # 构建完整 URL
            request = self.context.get('request')
            return request.build_absolute_uri(instance.path.url)
        return None

    def get_size(self, obj) -> str:
        return human_readable_size(obj.size)

    def get_related_content_type(self, obj) -> str | None:
        if obj.content_type:
            # 获取模型类的 verbose_name（中文名）
            model_class = obj.content_type.model_class()
            if model_class:
                return str(model_class._meta.verbose_name)
            else:
                return obj.content_type.model  # fallback 到 model 名称（如 'user'）
        return None

    def get_related_object(self, obj) -> str | None:
        """返回关联对象的 __str__ 表示"""
        related_obj = obj.get_related_object()
        return str(related_obj) if related_obj else None

    def create(self, validated_data):
        uploaded_file = validated_data.pop('path')
        folder = validated_data.pop('folder', '').strip('/')
        # 计算 MD5
        md5_hash = hashlib.md5()
        for chunk in uploaded_file.chunks():
            md5_hash.update(chunk)
        md5sum = md5_hash.hexdigest()

        # 提取文件信息
        name = uploaded_file.name
        size = str(uploaded_file.size)
        _, ext = os.path.splitext(name)
        file_suffix = ext.lower().lstrip('.')

        # 创建实例（暂不保存）
        validated_data = {
            **validated_data,
            "path": uploaded_file,
            "folder": folder,
            "name": name,
            "size": size,
            "md5sum": md5sum,
            "file_suffix": file_suffix,
        }
        return super().create(validated_data)

    class Meta:
        model = FileModel
        fields = "__all__"

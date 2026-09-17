from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django_restql.mixins import DynamicFieldsMixin
from rest_framework import serializers
from .models import UserModel
from ..file.models import FileModel


def _bind_avatar(user_instance, file_id):
    """将指定文件绑定为用户头像"""
    try:
        file_obj = FileModel.objects.select_for_update().get(id=file_id)
    except FileModel.DoesNotExist:
        raise serializers.ValidationError({'avatar_file_id': '指定的文件不存在'})

    content_type = ContentType.objects.get_for_model(UserModel)
    file_obj.content_type = content_type
    file_obj.object_id = user_instance.id
    file_obj.save(update_fields=['content_type', 'object_id'])


class UserSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    dept_name = serializers.CharField(source="dept.name", read_only=True, help_text="部门名称")

    avatar_path = serializers.SerializerMethodField(help_text="用户头像路径")

    def get_avatar_path(self, instance) -> str | None:
        avatar = instance.avatar.first()
        if avatar:
            # 获取相对 URL
            relative_url = avatar.path.url
            # 构建完整 URL
            request = self.context.get('request')
            return request.build_absolute_uri(relative_url)
        return None

    avatar_id = serializers.SerializerMethodField(help_text="用户头像ID")

    def get_avatar_id(self, instance) -> int | None:
        avatar = instance.avatar.first()
        return avatar.id if avatar else None

    dept_full_path = serializers.SerializerMethodField(help_text="部门全路径")

    def get_dept_full_path(self, instance) -> str | None:
        """
        返回用户所属部门的全路径（如 '总公司/研发部/后端组'）。

        查询优化：优先读取视图在 list 时批量注入的 _dept_full_path 缓存
        （由 annotate_dept_full_path() 恒定 2 次查询生成，避免逐行查询）；
        无缓存时（单对象场景如详情/新建回显）回退到模型方法 full_path()
        （1 次祖先查询），保证序列化器可独立复用。

        边界情况：用户未关联部门（dept=None）时返回 None。
        """
        cached = getattr(instance, "_dept_full_path", None)
        if cached is not None:
            # 批量注入时部门缺失注入空字符串，语义化为 None 保持输出一致
            return cached or None
        return instance.dept.full_path() if instance.dept else None

    role_name = serializers.SerializerMethodField(help_text="用户角色列表")

    def get_role_name(self, instance) -> str | None:
        return ", ".join(role.name for role in instance.role.all())

    class Meta:
        model = UserModel
        fields = [
            'id',
            'username',
            'name',
            'email',
            'mobile',
            'gender',
            'timezone',
            'dept',
            'role',
            'role_name',
            'dept_name',
            'dept_full_path',
            'avatar_id',
            'avatar_path',
            'is_staff',
            'is_active'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    avatar_id = serializers.IntegerField(write_only=True, required=False)

    def create(self, validated_data):
        avatar_id = validated_data.pop('avatar_id', None)
        with transaction.atomic():
            instance = super().create(validated_data)
            # 创建时：如果有头像 avatar_file_id，就绑定
            if avatar_id is not None and avatar_id > 0:
                _bind_avatar(instance, avatar_id)
        return instance

    class Meta:
        model = UserModel
        fields = [
            'username',
            'name',
            'email',
            'mobile',
            'gender',
            'timezone',
            'dept',
            'role',
            'avatar_id',
            'is_staff',
            'is_active'
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    avatar_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    def update(self, instance, validated_data):
        avatar_id = validated_data.pop('avatar_id', None)

        with transaction.atomic():
            updated_instance = super().update(instance, validated_data)

            # 更新时：仅当显式传了有效 avatar_file_id 才绑定
            if 'avatar_id' in self.initial_data:
                if avatar_id is not None and avatar_id > 0:
                    _bind_avatar(updated_instance, avatar_id)
                # 否则（如传了非正数或未传）—— 什么也不做，保留原头像

        return updated_instance

    class Meta:
        model = UserModel
        fields = [
            'id',
            'username',
            'name',
            'email',
            'mobile',
            'gender',
            'timezone',
            'dept',
            'role',
            'avatar_id',
            'is_staff',
            'is_active'
        ]

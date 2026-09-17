from rest_framework import serializers

from extends.drf.serializers import CustomSerializer
from .models import RoleModel


class RoleRetrieveSerializer(CustomSerializer):
    """
    角色详情序列化器：输出关联菜单 ID 列表与关联用户简要信息。

    N+1 优化：get_menus / get_users 遍历 prefetch_related 缓存中的对象，
    而非使用 values_list() / values() 创建新查询；
    视图层需在 retrieve 时通过 Prefetch('menu') + Prefetch('user', select_related('dept')) 预加载。
    """

    skip_field_permissions = True
    users = serializers.SerializerMethodField()
    menus = serializers.SerializerMethodField()

    def get_menus(self, instance) -> list:
        """获取关联菜单 ID 列表（利用 prefetch_related 缓存，零额外查询）。"""
        return [menu.id for menu in instance.menu.all()]

    def get_users(self, instance) -> list:
        """获取关联用户简要信息列表（利用 prefetch_related 缓存，零额外查询）。"""
        return [
            {"id": u.id, "name": u.name, "dept__name": u.dept.name if u.dept else None}
            for u in instance.user.all()
        ]

    class Meta:
        model = RoleModel
        fields = '__all__'


class RoleSerializer(CustomSerializer):
    """角色序列化器，包含用户数量统计字段。"""

    user_count = serializers.SerializerMethodField(read_only=True, help_text="用户数量")

    def get_user_count(self, instance) -> int:
        """获取关联用户数量。"""
        return instance.user.count()

    class Meta:
        model = RoleModel
        fields = '__all__'


class RoleCreateSerializer(CustomSerializer):
    class Meta:
        model = RoleModel
        fields = '__all__'


class RoleUpdateSerializer(CustomSerializer):
    class Meta:
        model = RoleModel
        fields = '__all__'

from rest_framework import serializers

from extends.drf.serializers import CustomSerializer
from .models import RoleMenuButtonModel


class RoleMenuButtonSerializer(CustomSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True, help_text="角色名称")
    menu_button_name = serializers.CharField(source="menu_button.name", read_only=True, help_text="菜单按钮名称")
    menu_button_key = serializers.CharField(source="menu_button.key", read_only=True, help_text="菜单按钮权限值")

    class Meta:
        model = RoleMenuButtonModel
        fields = '__all__'


class RoleMenuButtonCreateSerializer(CustomSerializer):
    """创建序列化器

    兜底规则：按钮不需要数据访问（need_data_scope=False）时，
    忽略传入的权限范围，强制默认为“全部”(4) 且不关联部门。
    """

    def validate(self, attrs):
        menu_button = attrs.get("menu_button")
        if menu_button is not None and not menu_button.need_data_scope:
            attrs["permission_range"] = 4
            attrs.pop("dept", None)
        return attrs

    class Meta:
        model = RoleMenuButtonModel
        fields = '__all__'


class RoleMenuButtonUpdateSerializer(CustomSerializer):
    class Meta:
        model = RoleMenuButtonModel
        fields = '__all__'

from rest_framework import serializers

from extends.drf.serializers import CustomSerializer
from .models import RoleMenuFieldModel


class RoleMenuFieldSerializer(CustomSerializer):
    """角色菜单字段序列化器：列表/详情接口使用，附带菜单与角色的冗余展示字段（避免前端逐层联查）。"""
    menu_title = serializers.CharField(source='menu_field.menu.title', help_text="菜单名称")
    menu_name = serializers.CharField(source='menu_field.menu.name', help_text="菜单路由名")
    menu_field_verbose_name = serializers.CharField(source='menu_field.verbose_name', help_text="字段显示名")
    menu_field_model = serializers.CharField(source='menu_field.model', help_text="字段所属模型表")
    menu_field_name = serializers.CharField(source='menu_field.field_name', help_text="字段名")
    role_name = serializers.CharField(source='role.name', help_text="角色名称")

    class Meta:
        model = RoleMenuFieldModel
        fields = '__all__'

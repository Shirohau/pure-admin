from rest_framework import serializers

from extends.drf.serializers import CustomSerializer
from .models import MenuModel


class MenuSerializer(CustomSerializer):
    parentId = serializers.IntegerField(source='parent_id', label="上级菜单ID")

    class Meta:
        model = MenuModel
        fields = '__all__'


class MenuRoutesSerializer(CustomSerializer):
    skip_field_permissions = True  # 跳过字段权限
    meta = serializers.SerializerMethodField()

    @staticmethod
    def get_meta(instance):
        return {
            "title": instance.title,
            "icon": instance.icon,
            "extraIcon": instance.extraIcon,
            "showLink": instance.showLink,
            "showParent": instance.showParent,
            "keepAlive": instance.keepAlive,
            "frameSrc": instance.frameSrc,
            "frameLoading": instance.frameLoading,
            "transition": {
                "name": instance.transitionName,
                "enterTransition": instance.enterTransition,
                "leaveTransition": instance.leaveTransition,
            },
            "hiddenTag": instance.hiddenTag,
            "fixedTag": instance.fixedTag,
        }

    class Meta:
        model = MenuModel
        fields = ["id", "parent", "path", "name", "component", "meta"]


class MenuCreateSerializer(CustomSerializer):
    class Meta:
        model = MenuModel
        fields = '__all__'


class MenuUpdateSerializer(CustomSerializer):
    class Meta:
        model = MenuModel
        fields = '__all__'

from extends.drf.serializers import CustomSerializer
from .models import MenuFieldModel


class MenuFieldSerializer(CustomSerializer):
    """菜单字段序列化器：列表/详情接口使用。"""



    class Meta:
        model = MenuFieldModel
        fields = '__all__'


class MenuFieldCreateSerializer(CustomSerializer):
    """菜单字段新增序列化器。"""

    class Meta:
        model = MenuFieldModel
        fields = '__all__'


class MenuFieldUpdateSerializer(CustomSerializer):
    """菜单字段更新序列化器。"""

    class Meta:
        model = MenuFieldModel
        fields = '__all__'

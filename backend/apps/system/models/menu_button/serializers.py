from extends.drf.serializers import CustomSerializer
from .models import MenuButtonModel


class MenuButtonSerializer(CustomSerializer):
    class Meta:
        model = MenuButtonModel
        fields = '__all__'


class MenuButtonCreateSerializer(CustomSerializer):
    class Meta:
        model = MenuButtonModel
        fields = '__all__'


class MenuButtonUpdateSerializer(CustomSerializer):
    class Meta:
        model = MenuButtonModel
        fields = '__all__'

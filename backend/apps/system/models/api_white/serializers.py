from extends.drf.serializers import CustomSerializer
from .models import ApiWhiteModel


class ApiWhiteSerializer(CustomSerializer):
    class Meta:
        model = ApiWhiteModel
        fields = '__all__'


class ApiWhiteCreateSerializer(CustomSerializer):
    class Meta:
        model = ApiWhiteModel
        fields = '__all__'


class ApiWhiteUpdateSerializer(CustomSerializer):
    class Meta:
        model = ApiWhiteModel
        fields = '__all__'

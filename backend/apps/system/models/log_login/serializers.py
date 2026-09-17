from extends.drf.serializers import CustomSerializer
from .models import LogLoginModel


class LogLoginSerializer(CustomSerializer):
    class Meta:
        model = LogLoginModel
        fields = "__all__"


class LogLoginCreateSerializer(CustomSerializer):
    class Meta:
        model = LogLoginModel
        fields = "__all__"


class LogLoginUpdateSerializer(CustomSerializer):
    class Meta:
        model = LogLoginModel
        fields = "__all__"

from extends.drf.serializers import CustomSerializer
from .models import LogRequestModel


class LogRequestSerializer(CustomSerializer):
    class Meta:
        model = LogRequestModel
        fields = "__all__"


class LogRequestCreateSerializer(CustomSerializer):
    class Meta:
        model = LogRequestModel
        fields = "__all__"


class LogRequestUpdateSerializer(CustomSerializer):
    class Meta:
        model = LogRequestModel
        fields = "__all__"

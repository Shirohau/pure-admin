from rest_framework import serializers

from extends.drf.serializers import CustomSerializer
from .models import AreaModel


class AreaSerializer(CustomSerializer):
    class Meta:
        model = AreaModel
        fields = '__all__'


class AreaCreateSerializer(CustomSerializer):
    class Meta:
        model = AreaModel
        fields = '__all__'


class AreaUpdateSerializer(CustomSerializer):
    class Meta:
        model = AreaModel
        fields = '__all__'

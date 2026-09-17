from extends.drf.serializers import CustomSerializer
from rest_framework import serializers
from .models import DictionaryModel


class DictionarySerializer(CustomSerializer):
    class Meta:
        model = DictionaryModel
        fields = '__all__'


class DictionaryCreateSerializer(CustomSerializer):
    class Meta:
        model = DictionaryModel
        fields = '__all__'


class DictionaryUpdateSerializer(CustomSerializer):
    class Meta:
        model = DictionaryModel
        fields = '__all__'


class DictionaryTreeSerializer(CustomSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = DictionaryModel
        fields = '__all__'

    def get_children(self, obj) -> list:
        children = getattr(obj, '_prefetched_children', None)
        if children is None:
            children = obj.children.filter(status=True)
        return DictionaryTreeSerializer(children, many=True, context=self.context).data

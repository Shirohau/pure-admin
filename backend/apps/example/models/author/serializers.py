from rest_framework import serializers

from extends.drf.serializers import CustomSerializer
from .models import AuthorModel
from ..book.models import BookModel


class AuthorBookSerializer(CustomSerializer):
    class Meta:
        model = BookModel
        # fields = '__all__'
        fields = ['id', 'name', 'price', 'updater_name']


class AuthorSerializer(CustomSerializer):
    book_row = AuthorBookSerializer(source="book", read_only=True, many=True, label="所有图书信息")
    book_count = serializers.IntegerField(read_only=True, label="图书数量")
    avg_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, label="平均价格")

    book = serializers.PrimaryKeyRelatedField(
        many=True, queryset=BookModel.objects.only('pk'),
        required=False, allow_null=True,
        help_text="关联的图书ID列表"
    )

    book_name = serializers.SerializerMethodField(label="图书名称")

    def get_book_name(self, obj) -> str:
        """多对多图书名称用逗号拼接"""
        return ", ".join(book.name for book in obj.book.all())

    class Meta:
        model = AuthorModel
        fields = '__all__'


class AuthorCreateSerializer(AuthorSerializer):

    def create(self, validated_data):
        book = validated_data.pop('book', None)
        instance = super().create(validated_data)
        if book:
            instance.book.add(*book)
        return instance

    class Meta:
        model = AuthorModel
        fields = '__all__'


class AuthorUpdateSerializer(AuthorSerializer):

    def update(self, instance, validated_data):
        book = validated_data.pop('book', None)
        instance = super().update(instance, validated_data)
        # book 为 None 表示未传，不做处理；传空列表 [] 表示取消所有关联
        if book is not None:
            instance.book.clear()
            instance.book.add(*book)
        return instance

    class Meta:
        model = AuthorModel
        fields = '__all__'

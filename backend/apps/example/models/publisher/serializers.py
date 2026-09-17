from django.utils import timezone
from rest_framework import serializers
from simple_history.utils import bulk_update_with_history

from extends.drf.serializers import CustomSerializer
from .models import PublisherModel
from ..book.models import BookModel


class PublisherBookSerializer(CustomSerializer):
    class Meta:
        model = BookModel
        # fields = '__all__'
        fields = ['id', 'name', 'price', 'updater_name']


class PublisherSerializer(CustomSerializer):
    book_all = PublisherBookSerializer(source="book", read_only=True, many=True, label="所有图书信息")
    book_count = serializers.IntegerField(read_only=True, label="图书数量")
    avg_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, label="平均价格")
    area_str = serializers.CharField(read_only=True, label="地区")

    book = serializers.PrimaryKeyRelatedField(
        many=True, queryset=BookModel.objects.only('pk'),
        required=False, allow_null=True,
        help_text="关联的图书ID列表，可不传"
    )

    book_name = serializers.SerializerMethodField(label="图书名称")

    def get_book_name(self, obj) -> str:
        """多对多图书名称用逗号拼接"""
        return ", ".join(book.name for book in obj.book.all())

    class Meta:
        model = PublisherModel
        fields = '__all__'


class PublisherCreateSerializer(PublisherSerializer):
    def create(self, validated_data):
        book = validated_data.pop('book', None)
        instance = super().create(validated_data)
        if book:
            user = self._get_user()
            now = timezone.now()
            for b in book:
                b.publisher = instance
                b.updater = user
                b.update_dt = now
            # 批量更新 + 批量创建历史记录（兼顾性能与审计）
            bulk_update_with_history(
                book, BookModel,
                fields=['publisher', 'updater', 'update_dt'],
                default_user=user,
            )
        return instance

    class Meta:
        model = PublisherModel
        fields = '__all__'


class PublisherUpdateSerializer(PublisherSerializer):
    def update(self, instance, validated_data):
        book = validated_data.pop('book', None)
        instance = super().update(instance, validated_data)
        # book 为 None 表示未传，不做处理；传空列表 [] 表示取消所有关联
        if book is not None:
            user = self._get_user()
            now = timezone.now()
            new_ids = [b.pk for b in book]

            # 1. 移除不在新列表中的旧关联（publisher 已改为 null=True）
            # 注意：exclude(pk__in=[]) 在 Django 中不会匹配任何记录，空列表时需取全部
            if new_ids:
                books_to_remove = list(instance.book.exclude(pk__in=new_ids))
            else:
                books_to_remove = list(instance.book.all())
            for b in books_to_remove:
                b.publisher = None
                b.updater = user
                b.update_dt = now
            if books_to_remove:
                bulk_update_with_history(
                    books_to_remove, BookModel,
                    fields=['publisher', 'updater', 'update_dt'],
                    default_user=user,
                )

            # 2. 批量关联新图书
            books_to_add = list(BookModel.objects.filter(pk__in=new_ids))
            for b in books_to_add:
                b.publisher = instance
                b.updater = user
                b.update_dt = now
            if books_to_add:
                bulk_update_with_history(
                    books_to_add, BookModel,
                    fields=['publisher', 'updater', 'update_dt'],
                    default_user=user,
                )
        return instance

    class Meta:
        model = PublisherModel
        fields = '__all__'

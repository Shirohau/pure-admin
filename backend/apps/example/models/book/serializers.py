#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：serializers.py
@Author  ：李小涛
@Date    ：2025/11/26 下午5:33 
@Explain : 图书 序列化
"""
from rest_framework import serializers

from extends.drf.serializers import CustomSerializer
from .models import BookModel
from ..author.serializers import AuthorSerializer
from ..publisher.serializers import PublisherSerializer


class PublisherPartialSerializer(PublisherSerializer):
    class Meta(PublisherSerializer.Meta):
        fields = ['id', 'name', 'updater_name']  # 只保留你需要的字段


class AuthorPartialSerializer(AuthorSerializer):
    class Meta(AuthorSerializer.Meta):
        fields = ['id', 'name', 'creator_name']  # 只保留你需要的字段


class BookSerializer(CustomSerializer):
    publisher_name = serializers.CharField(read_only=True, source="publisher.name", label="出版社名称")
    publisher_row = PublisherPartialSerializer(source="publisher", read_only=True, label="出版社信息")
    author_name = serializers.SerializerMethodField(label="作者名称")
    author_row = AuthorPartialSerializer(source="author", read_only=True, many=True, label="所有作者信息")

    def get_author_name(self, obj) -> str:
        """多对多作者姓名用逗号拼接"""
        return ", ".join(author.name for author in obj.author.all())

    class Meta:
        model = BookModel
        fields = '__all__'


class BookCreateSerializer(CustomSerializer):
    def create(self, validated_data):
        instance = super().create(validated_data)
        authors = validated_data.pop('author', None)
        if authors is not None:
            instance.author.set(authors)
        return instance

    class Meta:
        model = BookModel
        fields = '__all__'


class BookUpdateSerializer(CustomSerializer):

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # 提取多对多字段
        authors = validated_data.pop('author', None)
        # 更新多对多字段（必须在 instance 保存后）
        if authors is not None:
            instance.author.set(authors)

        return instance

    class Meta:
        model = BookModel
        fields = '__all__'

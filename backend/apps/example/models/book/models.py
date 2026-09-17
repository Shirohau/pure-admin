#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2025/11/26 下午5:27 
@Explain : 图书 数据表
"""

from django.core.validators import MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords

from apps.example.models import table_prefix
from extends.drf.models import CustomModel


class BookModel(CustomModel):
    # 一本书只能被一个出版社所出版
    publisher = models.ForeignKey(
        to="PublisherModel",
        related_name='book',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="出版社",
        db_comment="出版社",
        db_constraint=False,
    )
    # 一本书有多个作者，一个作者可以关联多本书
    author = models.ManyToManyField(
        to="AuthorModel",
        related_name='book',
        verbose_name="作者",
        db_constraint=False,
    )
    name = models.CharField(verbose_name="书名", db_comment="书名", max_length=128)
    isbn = models.CharField(verbose_name="ISBN", db_comment="ISBN", max_length=17, unique=True)
    publication_time = models.DateTimeField(verbose_name="出版时间", db_comment="出版时间", blank=True, null=True)
    # “价格”这个字段的值必须大于或等于 0，不允许负数
    price = models.DecimalField(verbose_name="价格", db_comment="价格", max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(0)])
    pages = models.PositiveIntegerField(verbose_name="页数", db_comment="页数", blank=True, null=True)
    description = models.TextField(verbose_name="内容简介", db_comment="内容简介", blank=True, null=True)

    # 历史记录
    history = HistoricalRecords(table_name=table_prefix + 'book_history', verbose_name="图书 历史记录")

    def __str__(self):
        return self.name

    class Meta:
        db_table = table_prefix + "book"
        verbose_name = "图书"
        db_table_comment = verbose_name
        verbose_name_plural = verbose_name
        ordering = ['-id']

from functools import reduce
from operator import and_

import django_filters
from django.db.models import Q

from extends.drf.filters import CustomFilter
from .models import PublisherModel


class PublisherFilter(CustomFilter):
    area = django_filters.CharFilter(
        method='filter_area',
        label='地区',
    )
    area__isnull = django_filters.BooleanFilter(
        method='filter_area_isnull',
        label='地区为空',
    )

    def filter_area(self, queryset, name, value):
        """
        地区筛选：前端传入路径字符串，支持多个路径（多选）

        格式说明：
            - 路径内：逗号分隔层级，按位置映射 province/city/district（如 "天津市,市辖区,和平区"）
            - 路径间：竖线 | 分隔多个路径，各路径 OR 连接（如 "天津市,市辖区,和平区|北京市,市辖区,东城区"）

        兼容性：单个路径时行为与旧版一致（逐层 AND 匹配）
        """
        if not value:
            return queryset

        fields = ['province', 'city', 'district']
        q = Q()
        # 先按 | 拆分为多个路径（多选），再按 , 拆分每个路径的层级
        for path in value.split('|'):
            parts = [p.strip() for p in path.split(',') if p.strip()]
            if not parts:
                continue
            # 单个路径内逐层 AND 匹配（如省=天津 且 市=市辖区 且 区=和平区）
            q |= reduce(and_, [Q(**{f: p}) for f, p in zip(fields, parts)], Q())
        return queryset.filter(q) if q else queryset

    def filter_area_isnull(self, queryset, name, value):
        """查找 province、city、district 均为空的记录"""
        if value:
            return queryset.filter(
                Q(province='') | Q(province__isnull=True),
                Q(city='') | Q(city__isnull=True),
                Q(district='') | Q(district__isnull=True),
            )
        return queryset

    class Meta(CustomFilter.Meta):
        model = PublisherModel

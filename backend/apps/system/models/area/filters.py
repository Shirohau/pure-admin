import django_filters

from extends.drf.filters import CustomFilter
from .models import AreaModel


class AreaFilter(CustomFilter):
    parent_code = django_filters.CharFilter(field_name="parent__code", label="父级编码")

    class Meta(CustomFilter.Meta):
        model = AreaModel

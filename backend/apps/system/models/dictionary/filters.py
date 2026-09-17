import django_filters

from extends.drf.filters import CustomFilter
from .models import DictionaryModel


class DictionaryFilter(CustomFilter):
    parent_value = django_filters.CharFilter(field_name='parent__value', label='父级值')

    class Meta(CustomFilter.Meta):
        model = DictionaryModel

import django_filters

from extends.drf.filters import CustomFilter
from .models import MessageCenter, MessageCenterTargetUser


class MessageCenterFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = MessageCenter


class MessageCenterTargetUserFilter(CustomFilter):
    is_read = django_filters.BooleanFilter(field_name='is_read')

    class Meta(CustomFilter.Meta):
        model = MessageCenterTargetUser

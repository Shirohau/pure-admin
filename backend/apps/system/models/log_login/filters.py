from extends.drf.filters import CustomFilter
from .models import LogLoginModel


class LogLoginFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = LogLoginModel

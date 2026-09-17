from extends.drf.filters import CustomFilter
from .models import LogRequestModel


class LogRequestFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = LogRequestModel

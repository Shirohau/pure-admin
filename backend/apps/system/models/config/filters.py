from extends.drf.filters import CustomFilter
from .models import ConfigModel


class ConfigFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = ConfigModel

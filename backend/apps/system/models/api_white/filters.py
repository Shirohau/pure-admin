from extends.drf.filters import CustomFilter
from .models import ApiWhiteModel


class ApiWhiteFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = ApiWhiteModel

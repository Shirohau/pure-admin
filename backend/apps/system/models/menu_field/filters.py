from extends.drf.filters import CustomFilter
from .models import MenuFieldModel


class MenuFieldFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = MenuFieldModel

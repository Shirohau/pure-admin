from extends.drf.filters import CustomFilter
from .models import MenuModel


class MenuFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = MenuModel

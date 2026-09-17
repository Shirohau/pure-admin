from extends.drf.filters import CustomFilter
from .models import MenuButtonModel


class MenuButtonFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = MenuButtonModel
        fields = "__all__"

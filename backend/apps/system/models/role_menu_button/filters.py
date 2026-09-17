from extends.drf.filters import CustomFilter
from .models import RoleMenuButtonModel


class RoleMenuButtonFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = RoleMenuButtonModel

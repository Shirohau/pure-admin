from extends.drf.filters import CustomFilter
from .models import RoleMenuFieldModel


class RoleMenuFieldFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = RoleMenuFieldModel

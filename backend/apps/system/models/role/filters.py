from extends.drf.filters import CustomFilter
from .models import RoleModel


class RoleFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = RoleModel

from extends.drf.filters import CustomFilter
from .models import UserModel


class UserFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = UserModel

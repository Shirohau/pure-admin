from extends.drf.filters import CustomFilter
from .models import UserOAuthModel


class UserOAuthFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = UserOAuthModel

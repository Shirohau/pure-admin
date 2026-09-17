from django.urls import path, include
from rest_framework import routers

from .views import RoleMenuButtonViewSet

router = routers.DefaultRouter()
router.register(r'rolemenubutton', RoleMenuButtonViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

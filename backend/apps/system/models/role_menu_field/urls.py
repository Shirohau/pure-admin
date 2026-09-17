from django.urls import path, include
from rest_framework import routers

from .views import RoleMenuFieldViewSet

router = routers.DefaultRouter()

router.register(r'rolemenufield', RoleMenuFieldViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

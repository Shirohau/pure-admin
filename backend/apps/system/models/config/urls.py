from django.urls import path, include
from rest_framework import routers

from .views import ConfigViewSet

router = routers.DefaultRouter()
router.register(r'config', ConfigViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

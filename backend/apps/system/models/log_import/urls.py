from django.urls import path, include
from rest_framework import routers

from .views import ExportJobViewSet

router = routers.DefaultRouter()
router.register(r"log_import", ExportJobViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

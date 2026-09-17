from django.urls import path, include
from rest_framework import routers

from .views import LogRequestViewSet, LogRequestExportJobViewSet, LogRequestImportJobViewSet

router = routers.DefaultRouter()
# router.register(r"logrequest/async_import", LogRequestImportJobViewSet)
router.register(r"log_request/async_export", LogRequestExportJobViewSet)
router.register(r"log_request", LogRequestViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

from django.urls import path, include
from rest_framework import routers

from .views import LogLoginViewSet, LogLoginExportJobViewSet, LogLoginImportJobViewSet

router = routers.DefaultRouter()
# router.register(r"loglogin/async_import", LogLoginImportJobViewSet)
router.register(r"log_login/async_export", LogLoginExportJobViewSet)
router.register(r"log_login", LogLoginViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

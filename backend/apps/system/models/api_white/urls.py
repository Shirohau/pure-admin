from django.urls import path, include
from rest_framework import routers

from .views import ApiWhiteViewSet, ApiWhiteExportJobViewSet, ApiWhiteImportJobViewSet

router = routers.DefaultRouter()
router.register(r'apiwhite/async_import', ApiWhiteImportJobViewSet)
router.register(r'apiwhite/async_export', ApiWhiteExportJobViewSet)
router.register(r'apiwhite', ApiWhiteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

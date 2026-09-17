from django.urls import path, include
from rest_framework import routers

from .views import AreaViewSet, AreaExportJobViewSet, AreaImportJobViewSet

router = routers.DefaultRouter()
router.register(r'area/async_import', AreaImportJobViewSet)
router.register(r'area/async_export', AreaExportJobViewSet)
router.register(r'area', AreaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

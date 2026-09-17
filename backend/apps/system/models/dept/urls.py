from django.urls import path, include
from rest_framework import routers

from .views import DeptViewSet, DeptExportJobViewSet, DeptImportJobViewSet

router = routers.DefaultRouter()
router.register(r'dept/async_import', DeptImportJobViewSet)
router.register(r'dept/async_export', DeptExportJobViewSet)
router.register(r'dept', DeptViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

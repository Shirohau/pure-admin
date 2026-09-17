from django.urls import path, include
from rest_framework import routers

from .views import RoleViewSet, RoleExportJobViewSet, RoleImportJobViewSet

router = routers.DefaultRouter()
# router.register(r'role/async_import', RoleImportJobViewSet)
# router.register(r'role/async_export', RoleExportJobViewSet)
router.register(r'role', RoleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

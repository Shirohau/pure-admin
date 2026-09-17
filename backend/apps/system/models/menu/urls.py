from django.urls import path, include
from rest_framework import routers

from .views import MenuViewSet, MenuExportJobViewSet, MenuImportJobViewSet

router = routers.DefaultRouter()
# router.register(r'menu/async_import', MenuImportJobViewSet)
# router.register(r'menu/async_export', MenuExportJobViewSet)
router.register(r'menu', MenuViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework import routers

from .views import MenuFieldViewSet, MenuFieldExportJobViewSet, MenuFieldImportJobViewSet

router = routers.DefaultRouter()
router.register(r'menufield/async_import', MenuFieldImportJobViewSet)
router.register(r'menufield/async_export', MenuFieldExportJobViewSet)
router.register(r'menufield', MenuFieldViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

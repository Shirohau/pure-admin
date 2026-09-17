from django.urls import path, include
from rest_framework import routers

from .views import MenuButtonViewSet, MenuButtonExportJobViewSet, MenuButtonImportJobViewSet

router = routers.DefaultRouter()
router.register(r'menubutton/async_import', MenuButtonImportJobViewSet)
router.register(r'menubutton/async_export', MenuButtonExportJobViewSet)
router.register(r'menubutton', MenuButtonViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

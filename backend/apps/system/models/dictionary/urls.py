from django.urls import path, include
from rest_framework import routers

from .views import DictionaryViewSet, DictionaryExportJobViewSet, DictionaryImportJobViewSet

router = routers.DefaultRouter()
router.register(r'dictionary/async_import', DictionaryImportJobViewSet)
router.register(r'dictionary/async_export', DictionaryExportJobViewSet)
router.register(r'dictionary', DictionaryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

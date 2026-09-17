from django.urls import path, include
from rest_framework import routers

from .views import PublisherViewSet, PublisherExportJobViewSet, PublisherImportJobViewSet

router = routers.DefaultRouter()
router.register(r'publisher/async_import', PublisherImportJobViewSet)
router.register(r'publisher/async_export', PublisherExportJobViewSet)
router.register(r'publisher', PublisherViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

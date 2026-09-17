from django.urls import path, include
from rest_framework import routers

from .views import AuthorViewSet, AuthorExportJobViewSet, AuthorImportJobViewSet

router = routers.DefaultRouter()
router.register(r'author/async_import', AuthorImportJobViewSet)
router.register(r'author/async_export', AuthorExportJobViewSet)
router.register(r'author', AuthorViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

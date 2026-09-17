from django.urls import path, include
from rest_framework import routers

from .views import UserViewSet, UserExportJobViewSet, UserImportJobViewSet

router = routers.DefaultRouter()
router.register(r'user/async_import', UserImportJobViewSet)
router.register(r'user/async_export', UserExportJobViewSet)
router.register(r'user', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

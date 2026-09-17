from django.urls import include, path
from rest_framework import routers

from .views import ExportFieldTemplateViewSet

router = routers.DefaultRouter()
router.register(r"export_field_template", ExportFieldTemplateViewSet)

urlpatterns = [path("", include(router.urls))]

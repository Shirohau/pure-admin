from django.urls import path, include
from rest_framework import routers

from .views import MessageCenterViewSet, MessageCenterTargetUserViewSet

router = routers.DefaultRouter()
router.register(r'message_center', MessageCenterViewSet)
router.register(r'message_center_target_user', MessageCenterTargetUserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

from rest_framework import routers

from .views import FlowInfoViewSet

router = routers.DefaultRouter()
router.register(r'info', FlowInfoViewSet)

urlpatterns = router.urls

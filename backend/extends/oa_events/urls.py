from django.urls import path
from .receiver import callback

urlpatterns = [path('callback/', callback)]

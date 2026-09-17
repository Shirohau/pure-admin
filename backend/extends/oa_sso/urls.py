from django.urls import path
from . import views

urlpatterns = [
    path('config/', views.configuration),
    path('prepare/', views.prepare),
    path('complete/', views.complete),
    path('logout/', views.logout),
]

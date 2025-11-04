"""
Papers API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaperViewSet

router = DefaultRouter()
router.register(r'', PaperViewSet, basename='paper')

urlpatterns = [
    path('', include(router.urls)),
]

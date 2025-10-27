"""
URL configuration for Patent Analysis System (PatentAI)
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # API 인증 (accounts 앱)
    path('api/accounts/', include('accounts.urls')),

    # API 문서 (drf-spectacular)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # 챗봇 API
    path('api/chatbot/', include('chatbot.urls')),

    # TODO: 다른 앱 URL 추가
    # path('api/patents/', include('patents.urls')),
    # path('api/chat/', include('chat.urls')),
    # path('api/history/', include('history.urls')),
]
if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
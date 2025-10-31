"""
챗봇 URL 설정
"""

from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # 메시지 전송
    path('send/', views.send_message, name='send-message'),

    # 대화 관리
    path('conversations/', views.list_conversations, name='list-conversations'),
    path('conversations/<uuid:conversation_id>/', views.conversation_detail, name='conversation-detail'),
    path('conversations/<uuid:conversation_id>/update-title/', views.update_conversation_title, name='update-title'),

    # 헬스체크
    path('health/', views.health_check, name='health-check'),
]

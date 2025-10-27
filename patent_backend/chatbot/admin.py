"""
챗봇 관리자 설정
"""

from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """대화 관리"""
    list_display = ['id', 'user', 'title', 'created_at', 'updated_at', 'message_count']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = '메시지 수'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """메시지 관리"""
    list_display = ['id', 'conversation', 'type', 'content_preview', 'file_name', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['content', 'conversation__title', 'conversation__user__username']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = '내용'

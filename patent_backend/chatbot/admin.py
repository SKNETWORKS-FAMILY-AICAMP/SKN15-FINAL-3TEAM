"""
챗봇 관리자 설정
"""

from django.contrib import admin
from django.utils import timezone
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """대화 관리"""
    list_display = ['id', 'user', 'title', 'created_at_kst', 'updated_at_kst', 'message_count']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'title']
    readonly_fields = ['id', 'created_at_kst', 'updated_at_kst']
    ordering = ['-updated_at']

    def created_at_kst(self, obj):
        """한국 시간으로 생성일 표시"""
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    created_at_kst.short_description = '생성일시 (KST)'
    created_at_kst.admin_order_field = 'created_at'

    def updated_at_kst(self, obj):
        """한국 시간으로 수정일 표시"""
        if obj.updated_at:
            local_time = timezone.localtime(obj.updated_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    updated_at_kst.short_description = '수정일시 (KST)'
    updated_at_kst.admin_order_field = 'updated_at'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = '메시지 수'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """메시지 관리"""
    list_display = ['id', 'conversation', 'type', 'content_preview', 'file_name', 'created_at_kst']
    list_filter = ['type', 'created_at']
    search_fields = ['content', 'conversation__title', 'conversation__user__username']
    readonly_fields = ['id', 'created_at_kst']
    ordering = ['-created_at']

    def created_at_kst(self, obj):
        """한국 시간으로 생성일 표시"""
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    created_at_kst.short_description = '생성일시 (KST)'
    created_at_kst.admin_order_field = 'created_at'

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = '내용'

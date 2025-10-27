"""
챗봇 모델
"""

from django.db import models
from accounts.models import User
import uuid


class Conversation(models.Model):
    """대화 세션"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, blank=True, default="새 대화")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = '대화'
        verbose_name_plural = '대화 목록'

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Message(models.Model):
    """대화 메시지"""
    MESSAGE_TYPES = (
        ('user', '사용자'),
        ('ai', 'AI'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_content = models.TextField(blank=True, null=True)  # 파일 텍스트 내용
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = '메시지'
        verbose_name_plural = '메시지 목록'

    def __str__(self):
        return f"{self.type}: {self.content[:50]}"

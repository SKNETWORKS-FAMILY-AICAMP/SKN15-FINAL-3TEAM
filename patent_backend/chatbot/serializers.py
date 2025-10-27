"""
챗봇 시리얼라이저
"""

from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    """메시지 시리얼라이저"""

    class Meta:
        model = Message
        fields = ['id', 'type', 'content', 'file_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    """대화 시리얼라이저"""
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages', 'message_count']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


class ConversationListSerializer(serializers.ModelSerializer):
    """대화 목록 시리얼라이저 (메시지 제외)"""
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'message_count', 'last_message']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'content': last_msg.content[:100],
                'type': last_msg.type,
                'created_at': last_msg.created_at
            }
        return None


class ChatRequestSerializer(serializers.Serializer):
    """챗봇 요청 시리얼라이저"""
    message = serializers.CharField(required=True)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    file_content = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    file_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class ChatResponseSerializer(serializers.Serializer):
    """챗봇 응답 시리얼라이저"""
    conversation_id = serializers.UUIDField()
    user_message = MessageSerializer()
    ai_message = MessageSerializer()

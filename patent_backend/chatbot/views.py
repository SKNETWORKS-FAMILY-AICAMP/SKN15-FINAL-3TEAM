"""
챗봇 뷰
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    ConversationListSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
    MessageSerializer
)
from .services import get_chat_service


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """
    챗봇에 메시지 전송 및 응답 받기

    Body:
        - message: 사용자 메시지 (필수)
        - conversation_id: 기존 대화 ID (선택, 없으면 새 대화 생성)
        - file_content: 업로드된 파일 내용 (선택)
        - file_name: 파일 이름 (선택)
    """
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    user = request.user
    message_text = data['message']
    conversation_id = data.get('conversation_id')
    file_content = data.get('file_content')
    file_name = data.get('file_name')

    # 대화 세션 가져오기 또는 생성
    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id, user=user)
    else:
        # 새 대화 생성
        conversation = Conversation.objects.create(
            user=user,
            title=message_text[:50]  # 첫 메시지의 앞 50자를 제목으로
        )

    # 사용자 메시지 저장
    user_message = Message.objects.create(
        conversation=conversation,
        type='user',
        content=message_text,
        file_name=file_name,
        file_content=file_content
    )

    # 이전 대화 내역 가져오기 (최근 10개만)
    conversation_history = []
    previous_messages = conversation.messages.exclude(id=user_message.id).order_by('-created_at')[:10]
    # 시간순으로 다시 정렬
    previous_messages = reversed(list(previous_messages))
    for msg in previous_messages:
        conversation_history.append({
            'type': msg.type,
            'content': msg.content
        })

    # AI 응답 생성
    chat_service = get_chat_service()
    ai_response_text = chat_service.generate_response(
        message=message_text,
        file_content=file_content,
        conversation_history=conversation_history
    )

    # AI 응답 메시지 저장
    ai_message = Message.objects.create(
        conversation=conversation,
        type='ai',
        content=ai_response_text
    )

    # 응답 반환
    response_data = {
        'conversation_id': conversation.id,
        'user_message': MessageSerializer(user_message).data,
        'ai_message': MessageSerializer(ai_message).data
    }

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_conversations(request):
    """
    대화 목록 조회

    Query Parameters:
        - my=true: 내 대화만 조회 (기본값)
        - my=false: 부서 전체 대화 조회
    """
    user = request.user
    my_only = request.query_params.get('my', 'true').lower() == 'true'

    if my_only:
        # 내 대화만
        conversations = Conversation.objects.filter(user=user)
    else:
        # 부서 전체 대화 (같은 회사, 같은 부서의 모든 사용자 대화)
        conversations = Conversation.objects.filter(
            user__company=user.company,
            user__department=user.department
        ).select_related('user')

    conversations = conversations.order_by('-updated_at')
    serializer = ConversationListSerializer(conversations, many=True)
    return Response(serializer.data)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    """
    특정 대화 조회 및 삭제
    - GET: 대화 상세 조회 (메시지 포함)
    - DELETE: 대화 삭제
    """
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)

    if request.method == 'GET':
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)

    elif request.method == 'DELETE':
        conversation.delete()
        return Response({'message': '대화가 삭제되었습니다.'}, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_conversation_title(request, conversation_id):
    """대화 제목 수정"""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    title = request.data.get('title')

    if not title:
        return Response({'error': '제목을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    conversation.title = title
    conversation.save()

    serializer = ConversationSerializer(conversation)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    """챗봇 서비스 상태 확인"""
    chat_service = get_chat_service()
    service_type = chat_service.__class__.__name__

    return Response({
        'status': 'ok',
        'service': service_type,
        'message': '챗봇 서비스가 정상 작동 중입니다.'
    })

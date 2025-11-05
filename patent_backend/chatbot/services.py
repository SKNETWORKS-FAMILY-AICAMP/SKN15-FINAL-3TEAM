"""
챗봇 서비스 레이어 - 모델 교체가 용이한 추상화 구조
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
import logging
import re
from django.conf import settings
# KoSBERT 관련 임포트 제거 (외부 모델 서버 사용)
# from .model_loader import get_kosbert_loader
# from .lunch_data import get_all_menu_items, get_random_menu, LUNCH_MENU

logger = logging.getLogger(__name__)


class BaseChatService(ABC):
    """챗봇 모델 인터페이스 - 모든 모델은 이 인터페이스를 구현해야 함"""

    @abstractmethod
    def generate_response(self, message: str, file_content: Optional[str] = None,
                         conversation_history: Optional[List[Dict]] = None) -> str:
        """
        사용자 메시지에 대한 응답 생성

        Args:
            message: 사용자 메시지
            file_content: 업로드된 파일 내용 (선택)
            conversation_history: 이전 대화 내역 (선택)

        Returns:
            AI 응답 텍스트
        """
        pass


class LlamaChatService(BaseChatService):
    """LLaMA 8B 모델 서빙 서버를 사용하는 챗봇 서비스"""

    def __init__(self):
        self.model_server_url = getattr(
            settings,
            'MODEL_SERVER_URL',
            'http://localhost:8001'
        )

    def generate_response(self, message: str, file_content: Optional[str] = None,
                         conversation_history: Optional[List[Dict]] = None) -> str:
        """LLaMA 모델 서버에 요청하여 응답 생성"""

        try:
            # 모델 서버에 POST 요청
            response = requests.post(
                f"{self.model_server_url}/generate",
                json={
                    "message": message,
                    "file_content": file_content,
                    "conversation_history": conversation_history,
                    "max_tokens": 512,
                    "temperature": 0.7
                },
                timeout=60  # 60초 타임아웃
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "응답을 받지 못했습니다.")
            else:
                return f"모델 서버 오류 (HTTP {response.status_code}): {response.text}"

        except requests.exceptions.ConnectionError:
            return "모델 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
        except requests.exceptions.Timeout:
            return "응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"


# KoSBERTChatService 클래스 제거됨
# 외부 모델 서버를 사용하려면 LlamaChatService 또는 CustomModelChatService를 사용하세요


class CustomModelChatService(BaseChatService):
    """사용자 정의 모델을 사용하는 챗봇 서비스"""

    def __init__(self):
        self.model_server_url = getattr(
            settings,
            'CUSTOM_MODEL_SERVER_URL',
            'http://localhost:8002'
        )

    def _build_prompt_with_history(self, message: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        멀티턴 대화를 위한 프롬프트 생성

        Args:
            message: 현재 사용자 메시지
            conversation_history: 이전 대화 내역

        Returns:
            멀티턴 컨텍스트가 포함된 프롬프트
        """
        if not conversation_history:
            return message

        # 대화 히스토리를 프롬프트에 포함
        prompt_parts = ["이전 대화 내역:"]
        for hist in conversation_history[-10:]:  # 최근 10개 대화만 사용
            role = "사용자" if hist['type'] == 'user' else "AI"
            prompt_parts.append(f"{role}: {hist['content']}")

        prompt_parts.append(f"\n현재 질문:\n사용자: {message}")
        prompt_parts.append("\nAI:")

        return "\n".join(prompt_parts)

    def generate_response(self, message: str, file_content: Optional[str] = None,
                         conversation_history: Optional[List[Dict]] = None) -> str:
        """커스텀 모델 서버에 요청하여 응답 생성 (멀티턴 지원)"""

        try:
            # 멀티턴 대화 히스토리를 포함한 프롬프트 생성
            prompt = self._build_prompt_with_history(message, conversation_history)

            # 모델 서버에 POST 요청
            response = requests.post(
                f"{self.model_server_url}/generate",
                json={
                    "prompt": prompt,
                    "message": message,  # 원본 메시지도 전달
                    "file_content": file_content,
                    "conversation_history": conversation_history,
                    "max_tokens": 512,
                    "temperature": 0.7
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "응답을 받지 못했습니다.")
            else:
                return f"모델 서버 오류 (HTTP {response.status_code}): {response.text}"

        except requests.exceptions.ConnectionError:
            return "모델 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
        except requests.exceptions.Timeout:
            return "응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"


class ChatServiceFactory:
    """챗봇 서비스 팩토리 - 설정에 따라 적절한 모델 선택"""

    @staticmethod
    def create_service() -> BaseChatService:
        """
        설정에 따라 적절한 챗봇 서비스 인스턴스 반환

        settings.CHATBOT_SERVICE 값에 따라:
        - 'llama': LLaMA 모델 (기본값)
        - 'custom': 사용자 정의 모델 (멀티턴 지원)
        """
        service_type = getattr(settings, 'CHATBOT_SERVICE', 'llama')

        if service_type == 'llama':
            return LlamaChatService()
        elif service_type == 'custom':
            return CustomModelChatService()
        else:
            # 기본값으로 LLaMA 사용
            logger.warning(f"알 수 없는 서비스 타입 '{service_type}', LLaMA 사용")
            return LlamaChatService()


# 싱글톤 패턴으로 서비스 인스턴스 관리
_chat_service_instance = None

def get_chat_service() -> BaseChatService:
    """챗봇 서비스 인스턴스를 반환 (싱글톤)"""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatServiceFactory.create_service()
    return _chat_service_instance

"""
챗봇 서비스 레이어 - 모델 교체가 용이한 추상화 구조
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from django.conf import settings


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


class ChatServiceFactory:
    """챗봇 서비스 팩토리 - 설정에 따라 적절한 모델 선택"""

    @staticmethod
    def create_service() -> BaseChatService:
        """
        설정에 따라 적절한 챗봇 서비스 인스턴스 반환

        settings.CHATBOT_SERVICE 값에 따라:
        - 'llama': LLaMA 8B 모델 (기본값)
        """
        service_type = getattr(settings, 'CHATBOT_SERVICE', 'llama')

        # 현재는 LLaMA만 지원
        return LlamaChatService()


# 싱글톤 패턴으로 서비스 인스턴스 관리
_chat_service_instance = None

def get_chat_service() -> BaseChatService:
    """챗봇 서비스 인스턴스를 반환 (싱글톤)"""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatServiceFactory.create_service()
    return _chat_service_instance

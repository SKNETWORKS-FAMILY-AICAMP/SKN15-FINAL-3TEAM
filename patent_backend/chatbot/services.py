"""
챗봇 서비스 레이어 - 모델 교체가 용이한 추상화 구조
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
import logging
import re
from django.conf import settings
from .lunch_data import get_all_menu_items, get_random_menu, get_menu_by_category, get_random_menu_by_category, LUNCH_MENU
from .rag_service import RAGService

logger = logging.getLogger(__name__)


def detect_lunch_request(message: str) -> tuple[bool, str]:
    """
    점심 메뉴 추천 요청인지 감지

    Returns:
        (is_lunch_request, category): 점심 요청 여부와 카테고리
    """
    message_lower = message.lower()

    # 점심 관련 키워드
    lunch_keywords = ['점심', '메뉴', '뭐 먹', '뭐먹', '먹을까', '식사', '밥', '저녁']

    # 카테고리 키워드
    category_map = {
        '한식': ['한식', '한국', '김치', '된장', '비빔밥', '제육'],
        '중식': ['중식', '중국', '짜장', '짬뽕', '탕수육'],
        '일식': ['일식', '일본', '초밥', '회', '라멘', '우동', '돈카츠'],
        '양식': ['양식', '파스타', '피자', '스테이크', '햄버거'],
        '분식': ['분식', '떡볶이', '라면', '김밥'],
    }

    # 점심 요청인지 확인
    is_lunch = any(keyword in message_lower for keyword in lunch_keywords)

    if not is_lunch:
        return False, None

    # 카테고리 감지
    for category, keywords in category_map.items():
        if any(keyword in message_lower for keyword in keywords):
            return True, category

    return True, None  # 카테고리 없이 점심 요청


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

        # 점심 메뉴 요청인지 먼저 확인
        is_lunch, category = detect_lunch_request(message)

        if is_lunch:
            if category:
                # 특정 카테고리 요청
                menus = get_random_menu_by_category(category, 3)
                return f"오늘 {category} 메뉴 추천드립니다:\n" + "\n".join(f"• {menu}" for menu in menus)
            else:
                # 전체 메뉴에서 랜덤
                menus = get_random_menu(3)
                return f"오늘의 점심 메뉴 추천드립니다:\n" + "\n".join(f"• {menu}" for menu in menus)

        try:
            # Qwen Chat Template 형식으로 프롬프트 구성
            system_msg = "You are a helpful assistant. Answer concisely in Korean. Do not repeat the question or add unnecessary explanations."

            # 대화 기록 필터링
            recent_history = []
            if conversation_history and len(conversation_history) > 0:
                for msg in conversation_history[-6:]:
                    content = msg.get('content', '')
                    # 점심 메뉴, 에러 메시지 제외
                    if ('점심' not in content and '메뉴' not in content and
                        not content.startswith('모델 서버 오류') and
                        not content.startswith('오늘') and
                        '먹' not in content):
                        recent_history.append(msg)
                recent_history = recent_history[-3:]  # 최근 3개만

            # Qwen Chat Template 구성
            prompt_parts = [f"<|im_start|>system\n{system_msg}<|im_end|>"]

            # 대화 기록 추가
            for msg in recent_history:
                role = "user" if msg['type'] == 'user' else "assistant"
                prompt_parts.append(f"<|im_start|>{role}\n{msg['content']}<|im_end|>")

            # 현재 사용자 메시지
            prompt_parts.append(f"<|im_start|>user\n{message}<|im_end|>")
            prompt_parts.append("<|im_start|>assistant")

            prompt = "\n".join(prompt_parts)

            # 모델 서버에 POST 요청
            response = requests.post(
                f"{self.model_server_url}/generate",
                json={
                    "prompt": prompt,
                    "max_length": 128,
                    "temperature": 0.7
                },
                timeout=300
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


class RAGChatService(BaseChatService):
    """RAG 기반 특허 검색 챗봇 서비스"""

    def __init__(self):
        # OpenAI 사용 여부 확인
        use_openai = os.getenv('USE_OPENAI_RAG', 'false').lower() == 'true'

        if use_openai:
            from .openai_rag_service import OpenAIRAGService
            self.rag_service = OpenAIRAGService()
            self.use_openai = True
            logger.info("✅ OpenAI RAG 서비스 사용")
        else:
            self.rag_service = RAGService()
            self.use_openai = False
            logger.info("✅ Runpod RAG 서비스 사용")

        self.model_server_url = getattr(
            settings,
            'MODEL_SERVER_URL',
            'http://localhost:8001'
        )

    def _detect_patent_search(self, message: str) -> bool:
        """특허 검색 요청인지 감지"""
        keywords = [
            '특허', '유사', '검색', '찾아', '관련',
            '비슷한', 'patent', 'similar', 'search'
        ]
        return any(keyword in message.lower() for keyword in keywords)

    def generate_response(self, message: str, file_content: Optional[str] = None,
                         conversation_history: Optional[List[Dict]] = None) -> str:
        """RAG를 사용한 응답 생성"""

        # 점심 메뉴 요청인지 먼저 확인
        is_lunch, category = detect_lunch_request(message)
        if is_lunch:
            if category:
                menus = get_random_menu_by_category(category, 3)
                return f"오늘 {category} 메뉴 추천드립니다:\n" + "\n".join(f"• {menu}" for menu in menus)
            else:
                menus = get_random_menu(3)
                return f"오늘의 점심 메뉴 추천드립니다:\n" + "\n".join(f"• {menu}" for menu in menus)

        # 특허 검색 요청인지 확인
        if self._detect_patent_search(message):
            try:
                # OpenAI 사용 시 전체 파이프라인을 한 번에 처리
                if self.use_openai:
                    return self.rag_service.rag_pipeline(
                        query=message,
                        use_classification=True,
                        top_k=3
                    )

                # Runpod 사용 시 기존 로직
                # RAG 검색 수행
                search_results = self.rag_service.search(message, top_k=3)

                if not search_results:
                    return "죄송합니다. 관련된 특허를 찾지 못했습니다."

                # Runpod 모델 서버의 /rag/pipeline 엔드포인트 사용
                # RAG → 분류 → LLM 전체 파이프라인 실행
                try:
                    response = requests.post(
                        f"{self.model_server_url}/rag/pipeline",
                        json={
                            "query": message,
                            "patents": search_results,
                            "use_classification": True,  # 분류 모델 사용
                            "max_length": 512
                        },
                        timeout=120  # 파이프라인은 시간이 더 걸릴 수 있음
                    )

                    if response.status_code == 200:
                        data = response.json()
                        return data.get('response', '응답 생성 실패')
                    else:
                        # 파이프라인 실패 시 검색 결과만 반환
                        context = "\n\n".join([
                            f"[특허 {i+1}] {result['application_number']}\n"
                            f"제목: {result['title_ko']}\n"
                            f"IPC: {result['ipc']}\n"
                            f"유사도: {result['similarity']:.2%}\n"
                            f"내용: {result['text'][:300]}..."
                            for i, result in enumerate(search_results)
                        ])
                        return f"관련 특허 {len(search_results)}개를 찾았습니다:\n\n{context}"

                except requests.exceptions.RequestException as e:
                    logger.error(f"모델 서버 파이프라인 실패: {e}")
                    # 모델 서버 연결 실패 시 검색 결과만 반환
                    context = "\n\n".join([
                        f"[특허 {i+1}] {result['application_number']}\n"
                        f"제목: {result['title_ko']}\n"
                        f"유사도: {result['similarity']:.2%}"
                        for i, result in enumerate(search_results)
                    ])
                    return f"관련 특허 {len(search_results)}개를 찾았습니다:\n\n{context}"

            except Exception as e:
                logger.error(f"RAG 검색 실패: {e}")
                return f"특허 검색 중 오류가 발생했습니다: {str(e)}"

        # 일반 질문은 기존 LLaMA 서비스 사용
        else:
            try:
                # Qwen Chat Template 형식으로 프롬프트 구성
                system_msg = "You are a helpful assistant. Answer concisely in Korean. Do not repeat the question or add unnecessary explanations."

                # 대화 기록 필터링
                recent_history = []
                if conversation_history and len(conversation_history) > 0:
                    for msg in conversation_history[-6:]:
                        content = msg.get('content', '')
                        # 점심 메뉴, 에러 메시지 제외
                        if ('점심' not in content and '메뉴' not in content and
                            not content.startswith('모델 서버 오류') and
                            not content.startswith('오늘의') and
                            '먹' not in content and
                            not content.startswith('죄송합니다')):
                            recent_history.append(msg)
                    recent_history = recent_history[-3:]  # 최근 3개만

                # Qwen Chat Template 구성
                prompt_parts = [f"<|im_start|>system\n{system_msg}<|im_end|>"]

                # 대화 기록 추가
                for msg in recent_history:
                    role = "user" if msg['type'] == 'user' else "assistant"
                    prompt_parts.append(f"<|im_start|>{role}\n{msg['content']}<|im_end|>")

                # 현재 사용자 메시지
                prompt_parts.append(f"<|im_start|>user\n{message}<|im_end|>")
                prompt_parts.append("<|im_start|>assistant")

                prompt = "\n".join(prompt_parts)

                response = requests.post(
                    f"{self.model_server_url}/generate",
                    json={
                        "prompt": prompt,
                        "max_length": 128,
                        "temperature": 0.7
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get('response', '응답 생성 실패')
                else:
                    return "죄송합니다. 응답 생성에 실패했습니다."

            except requests.exceptions.RequestException as e:
                logger.error(f"모델 서버 연결 실패: {e}")
                return "죄송합니다. 현재 AI 서비스에 연결할 수 없습니다."


class ChatServiceFactory:
    """챗봇 서비스 팩토리 - 설정에 따라 적절한 모델 선택"""

    @staticmethod
    def create_service() -> BaseChatService:
        """
        설정에 따라 적절한 챗봇 서비스 인스턴스 반환

        settings.CHATBOT_SERVICE 값에 따라:
        - 'llama': LLaMA 모델 (기본값)
        - 'custom': 사용자 정의 모델 (멀티턴 지원)
        - 'rag': RAG 기반 특허 검색 챗봇
        """
        service_type = getattr(settings, 'CHATBOT_SERVICE', 'rag')

        if service_type == 'llama':
            return LlamaChatService()
        elif service_type == 'custom':
            return CustomModelChatService()
        elif service_type == 'rag':
            return RAGChatService()
        else:
            # 기본값으로 RAG 사용
            logger.warning(f"알 수 없는 서비스 타입 '{service_type}', RAG 사용")
            return RAGChatService()


# 싱글톤 패턴으로 서비스 인스턴스 관리
_chat_service_instance = None

def get_chat_service() -> BaseChatService:
    """챗봇 서비스 인스턴스를 반환 (싱글톤)"""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatServiceFactory.create_service()
    return _chat_service_instance

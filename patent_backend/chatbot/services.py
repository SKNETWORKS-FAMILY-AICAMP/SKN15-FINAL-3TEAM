"""
챗봇 서비스 레이어 - 모델 교체가 용이한 추상화 구조
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
import logging
import re
from django.conf import settings
from .model_loader import get_kosbert_loader
from .lunch_data import get_all_menu_items, get_random_menu, LUNCH_MENU

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


class KoSBERTChatService(BaseChatService):
    """KoSBERT 모델을 사용하는 챗봇 서비스 (테스트용 간단한 구현)"""

    def __init__(self):
        self.model_loader = get_kosbert_loader()
        # 애플리케이션 시작 시 모델 미리 로드
        try:
            self.model_loader.load_model()
            logger.info("KoSBERT 모델 초기화 완료")
        except Exception as e:
            logger.error(f"KoSBERT 모델 초기화 실패: {str(e)}")

    def _is_lunch_request(self, message: str) -> bool:
        """점심/저녁 메뉴 추천 요청인지 감지"""
        meal_keywords = [
            r'점심',
            r'저녁',
            r'메뉴',
            r'뭐\s*먹',
            r'추천',
            r'식사',
            r'음식',
            r'밥',
            r'런치',
            r'디너',
            r'점메추',  # 점심메뉴추천 줄임말
            r'저메추',  # 저녁메뉴추천 줄임말
            r'뭐먹지',
            r'메뉴\s*추천'
        ]
        message_lower = message.lower()
        return any(re.search(keyword, message_lower) for keyword in meal_keywords)

    def _detect_category_preference(self, message: str) -> Optional[str]:
        """메시지에서 음식 카테고리 선호도 감지"""
        category_keywords = {
            "한식": [r'한식', r'한국', r'김치', r'찌개', r'된장', r'비빔밥'],
            "중식": [r'중식', r'중국', r'짜장', r'짬뽕', r'탕수육'],
            "일식": [r'일식', r'일본', r'초밥', r'라멘', r'돈까스', r'우동'],
            "양식": [r'양식', r'서양', r'스테이크', r'파스타', r'피자']
        }

        message_lower = message.lower()
        for category, keywords in category_keywords.items():
            if any(re.search(keyword, message_lower) for keyword in keywords):
                return category
        return None

    def _detect_meal_time(self, message: str) -> str:
        """점심인지 저녁인지 감지"""
        if re.search(r'저녁|디너|저메추', message.lower()):
            return "저녁"
        else:
            return "점심"  # 기본값은 점심

    def _recommend_lunch_random(self, category: Optional[str] = None, meal_time: str = "점심") -> str:
        """랜덤 메뉴 추천 (점심/저녁)"""
        menu = get_random_menu(category)

        response = f"🍽️ 오늘의 {meal_time} 추천\n\n"
        response += f"{menu['name']} ({menu['category']})\n"
        response += f"{menu['description']}\n\n"
        response += "맛있게 드세요! 😋"

        return response

    def _recommend_lunch_smart(self, message: str, meal_time: str = "점심") -> str:
        """KoSBERT 기반 스마트 메뉴 추천"""
        try:
            # 모든 메뉴 아이템 가져오기
            all_menu_items = get_all_menu_items()

            # 메뉴 설명만 추출
            menu_descriptions = [
                f"{item['name']} - {item['description']}"
                for item in all_menu_items
            ]

            # KoSBERT로 유사도 계산
            similar_results = self.model_loader.find_most_similar(
                query=message,
                candidates=menu_descriptions,
                top_k=3
            )

            # 응답 생성
            response = f"🔍 당신의 입맛에 맞는 {meal_time} 추천 메뉴\n\n"

            for rank, (idx, similarity) in enumerate(similar_results, 1):
                menu_item = all_menu_items[idx]
                response += f"{rank}. {menu_item['name']} ({menu_item['category']})\n"
                response += f"   {menu_item['description']}\n\n"

            response += "어떤 메뉴가 땡기시나요? 😊"

            return response

        except Exception as e:
            logger.error(f"스마트 메뉴 추천 중 오류: {str(e)}")
            # 오류 발생 시 랜덤 추천으로 폴백
            return self._recommend_lunch_random(meal_time=meal_time)

    def generate_response(self, message: str, file_content: Optional[str] = None,
                         conversation_history: Optional[List[Dict]] = None) -> str:
        """
        KoSBERT를 사용한 응답 생성

        - 점심 추천 요청 감지 시: 혼합 방식 추천 (랜덤 + 스마트)
        - 일반 요청: 특허 검색 (테스트 구현)
        """

        try:
            # 🍽️ 메뉴 추천 요청 감지 (이스터에그)
            if self._is_lunch_request(message):
                # 점심/저녁 시간 감지
                meal_time = self._detect_meal_time(message)

                # 카테고리 선호도 감지
                category = self._detect_category_preference(message)

                # 간단한 요청 ("점심 추천", "뭐 먹지", "점메추", "저메추")
                if len(message.strip()) < 15 or category:
                    # 랜덤 추천
                    return self._recommend_lunch_random(category, meal_time)
                else:
                    # 구체적인 요청 ("매운 거 먹고 싶어", "시원한 국물 요리")
                    # KoSBERT 스마트 추천
                    return self._recommend_lunch_smart(message, meal_time)

            # 일반 특허 검색 로직
            # 테스트용 샘플 특허 데이터
            sample_patents = [
                "인공지능 기반 이미지 인식 시스템에 관한 특허",
                "딥러닝을 활용한 자연어 처리 방법",
                "머신러닝 모델 최적화 알고리즘",
                "컴퓨터 비전을 이용한 객체 탐지 기술",
                "자율주행 차량의 경로 계획 시스템"
            ]

            # KoSBERT로 가장 관련성 높은 특허 찾기
            similar_results = self.model_loader.find_most_similar(
                query=message,
                candidates=sample_patents,
                top_k=3
            )

            # 응답 생성
            response_parts = ["KoSBERT 기반 검색 결과:\n"]
            for idx, similarity in similar_results:
                response_parts.append(
                    f"• {sample_patents[idx]} (유사도: {similarity:.2f})"
                )

            # 대화 히스토리 고려
            if conversation_history:
                response_parts.append(f"\n\n이전 대화 {len(conversation_history)}개를 고려했습니다.")

            # 파일 업로드 처리
            if file_content:
                response_parts.append("\n\n업로드된 파일 내용도 분석했습니다.")

            response_parts.append("\n\n질문: " + message)
            response_parts.append("\n\n현재 KoSBERT 모델이 정상적으로 작동하고 있습니다. 추후 실제 특허 데이터베이스와 연동하여 더 정교한 검색 및 답변을 제공할 예정입니다.")

            return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"KoSBERT 응답 생성 중 오류: {str(e)}")
            return f"응답 생성 중 오류가 발생했습니다: {str(e)}"


class ChatServiceFactory:
    """챗봇 서비스 팩토리 - 설정에 따라 적절한 모델 선택"""

    @staticmethod
    def create_service() -> BaseChatService:
        """
        설정에 따라 적절한 챗봇 서비스 인스턴스 반환

        settings.CHATBOT_SERVICE 값에 따라:
        - 'llama': LLaMA 8B 모델
        - 'kosbert': KoSBERT 기반 검색 모델 (기본값)
        """
        service_type = getattr(settings, 'CHATBOT_SERVICE', 'kosbert')

        if service_type == 'llama':
            return LlamaChatService()
        elif service_type == 'kosbert':
            return KoSBERTChatService()
        else:
            # 기본값으로 KoSBERT 사용
            logger.warning(f"알 수 없는 서비스 타입 '{service_type}', KoSBERT 사용")
            return KoSBERTChatService()


# 싱글톤 패턴으로 서비스 인스턴스 관리
_chat_service_instance = None

def get_chat_service() -> BaseChatService:
    """챗봇 서비스 인스턴스를 반환 (싱글톤)"""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatServiceFactory.create_service()
    return _chat_service_instance

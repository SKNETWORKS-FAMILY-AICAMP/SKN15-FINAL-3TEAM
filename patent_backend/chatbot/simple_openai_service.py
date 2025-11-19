"""
간단한 OpenAI 챗봇 서비스
RAG, 분류 없이 순수 OpenAI만 사용
"""
import os
import logging
from typing import List, Dict, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class SimpleOpenAIChatService:
    """순수 OpenAI 챗봇 서비스 (RAG 없음)"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"  # 빠르고 저렴

        logger.info("✅ Simple OpenAI 챗봇 서비스 초기화 완료")

    def generate_response(
        self,
        message: str,
        file_content: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        OpenAI GPT로 바로 응답 생성
        """
        try:
            # 대화 기록 구성
            messages = [
                {
                    "role": "system",
                    "content": "당신은 친절한 AI 어시스턴트입니다. 한국어로 답변하세요."
                }
            ]

            # 이전 대화 기록 추가 (최근 5개만)
            if conversation_history:
                for msg in conversation_history[-5:]:
                    role = "user" if msg.get('type') == 'user' else "assistant"
                    messages.append({
                        "role": role,
                        "content": msg.get('content', '')
                    })

            # 파일 내용이 있으면 추가
            if file_content:
                message = f"[첨부 파일 내용]\n{file_content[:2000]}\n\n[사용자 질문]\n{message}"

            # 현재 메시지 추가
            messages.append({
                "role": "user",
                "content": message
            })

            logger.info(f"OpenAI 요청: {message[:50]}...")

            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            answer = response.choices[0].message.content.strip()
            logger.info(f"OpenAI 응답 성공: {len(answer)} 글자")

            return answer

        except Exception as e:
            logger.error(f"OpenAI API 오류: {e}")
            return f"죄송합니다. 오류가 발생했습니다: {str(e)}"

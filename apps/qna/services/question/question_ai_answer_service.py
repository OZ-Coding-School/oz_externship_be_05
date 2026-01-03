import logging
import os
from typing import Any, cast

from google import genai
from google.genai import types

from apps.qna.models import Question
from apps.qna.models.question.question_ai_answer import QuestionAIAnswer

"""
Question AI Answer 서비스

질문 등록 시 AI 최초 답변을 자동 생성하는 서비스
Signal에서 Celery Task 통해 호출, DB 저장
"""

logger = logging.getLogger(__name__)

"""
Usage:
    service = QuestionAIAnswerService(question)
    ai_answer = service.generate()
"""
class QuestionAIAnswerService:
    SYSTEM_PROMPT = """
    당신은 AI 튜터입니다.
    학생들의 질문에 친절하고 정확하게 답변해주세요.
    답변 작성 시 다음 사항을 지켜주세요:
    - 명확하고 이해하기 쉬운 설명
    - 존댓말 사용
    - 필요한 경우 코드 예시 포함
    - 관련된 추가 학습 포인트 제안
    """

    def __init__(self, question: Question, using_model: str) -> None:
        self.question = question
        self.model = using_model

    @staticmethod
    def _get_api_key() -> str:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        return api_key

    @staticmethod
    def _get_client() -> genai.Client:
        return genai.Client(api_key=QuestionAIAnswerService._get_api_key())

    def _build_contents(self) -> list[types.Content]:
        user_message = f"""
        [질문 제목]
        {self.question.title}
        
        [질문 내용]
        {self.question.content}
        """
        return [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=self.SYSTEM_PROMPT),
                    types.Part.from_text(text=user_message),
                ]
            )
        ]
    def _generate_response(self) -> str:
        client=self._get_client()
        contents = self._build_contents()
        api_contents = cast(Any, contents)
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=api_contents,
            )

            if response.text:
                return response.text

            logger.warning("Empty response from Gemini API | question.id: %s, model: %s",
                           self.question.id, self.model)
            raise ValueError(
                f"AI 응답이 비어있음.\nquestion.id: {self.question.id}, model: {self.model}"
            )

        except ValueError:
            # 위에서 발생한 ValueError를 그대로 전달
            raise

        except Exception as e:
            error_msg = (
                f"Gemini API 호출 실패 | "
                f"question.id: {self.question.id}"
                f"model: {self.model}"
                f"error_type: {type(e).__name__}"
                f"error_detail: {str(e)}"
            )
            logger.exception(error_msg)
            raise RuntimeError(error_msg) from e

    def generate(self) -> QuestionAIAnswer:
        output = self._generate_response()
        ai_answer = QuestionAIAnswer.objects.create(
            question=self.question,
            output=output,
            using_model=self.model,
        )
        logger.info(
            "AI answer generated for question %s (answer_id: %s)",
            self.question.id,
            ai_answer.id,
        )
        return ai_answer

# 질문에 대한 AI 답변 생성 + 저장
def generate_ai_answer(
    question: Question,
    using_model: str,
) -> QuestionAIAnswer:
    service = QuestionAIAnswerService(question, using_model)
    return service.generate()

# 질문의 AI 답변 조회 (없으면 None)
def get_ai_answer(question: Question) -> QuestionAIAnswer | None:
    return QuestionAIAnswer.objects.filter(question=question).first()
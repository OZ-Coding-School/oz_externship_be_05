import logging

from celery import shared_task
from apps.chatbot.models.chatbot_sessions import ChatModel

"""
Question AI Answer Celery Tasks
Question 생성 시 Signal에서 호출되어 AI 답변을 비동기로 생성합니다.
Tasks:
    generate_ai_answer_task: AI 답변 생성 태스크
"""

logger = logging.getLogger(__name__)

"""
AI 답변 생성 Celery Task
Args:
    question_id: Question PK
    using_model: 사용할 AI 모델 (기본값: gemini-2.5-flash)
Returns:
    생성된 QuestionAIAnswer의 ID 또는 None (실패 시)
"""

def resolve_using_model(using_model: str) -> str:
    if using_model:
        return using_model
    else:
        return "gemini-2.5-flash"

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=40,
)
def generate_ai_answer_task(self, question_id: int, using_model: str) -> int | None:
    from apps.qna.models import Question
    from apps.qna.models.question.question_ai_answer import QuestionAIAnswer
    from apps.qna.services.question.question_ai_answer_service import generate_ai_answer

    resolved_model = resolve_using_model(using_model)

    logger.info(
        "AI answer generation started | question_id=%s, model=%s, attempt=%s",
        question_id,
        using_model,
        self.request.retries + 1,
    )

    try:
        # Question 조회
        question = Question.objects.get(id=question_id)

        # 이미 해당 모델로 생성된 답변이 있는지 확인
        existing = QuestionAIAnswer.objects.filter(
            question=question,
            using_model=resolved_model,
        ).first()

        if existing:
            logger.info(
                "AI answer already exists | question_id=%s, model=%s, answer_id=%s",
                question_id,
                resolved_model,
                existing.id,
            )
            return existing.id

        # AI 답변 생성
        ai_answer = generate_ai_answer(question, resolved_model)

        logger.info(
            "AI answer generation completed | question_id=%s, model=%s, answer_id=%s",
            question_id,
            resolved_model,
            ai_answer.id,
        )

        return ai_answer.id

    except Question.DoesNotExist:
        logger.error(
            "Question not found | question_id=%s",
            question_id,
        )
        return None

    except Exception as e:
        logger.exception(
            "AI answer generation failed | question_id=%s, model=%s, error=%s",
            question_id,
            resolved_model,
            str(e),
        )

        # 재시도
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(
                "AI answer generation max retries exceeded | question_id=%s, model=%s",
                question_id,
                resolved_model,
            )
            return None
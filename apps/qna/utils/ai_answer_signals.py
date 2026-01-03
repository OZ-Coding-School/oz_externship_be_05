import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.qna.models import Question

logger = logging.getLogger(__name__)

"""
Question Signals
Question 생성 이벤트 감지 → AI 최초 답변 생성 트리거.
Signals:
    on_question_created: Question 생성 시 AI 답변 자동 생성
"""

@receiver(post_save, sender=Question)
def on_question_created(
        sender: type[Question],
        instance: Question,
        created: bool,
        **kwargs,
) -> None:
    if not created:
        return

    # 지연 import (순환 참조 방지)
    from apps.qna.utils.ai_answer_tasks import generate_ai_answer_task, resolve_using_model

    raw_model = getattr(instance, "using_model", None)
    resolved_model = resolve_using_model(raw_model)

    def trigger_task() -> None:
        logger.info(
            "Triggering AI answer generation | question_id=%s, title=%s",
            instance.id,
            resolved_model,
            (getattr(instance, "title", "") or "")[:30],
        )
        generate_ai_answer_task.delay(instance.id, resolved_model)

    # 트랜잭션 커밋 후 태스크 실행 (DB에 Question이 확실히 저장된 후)
    transaction.on_commit(trigger_task)
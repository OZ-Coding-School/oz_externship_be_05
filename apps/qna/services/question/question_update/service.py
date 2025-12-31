from typing import Any

from django.db import transaction

from apps.qna.models import Question
from apps.qna.services.question.question_image_service import sync_question_images


@transaction.atomic
def update_question(
    *,
    question: Question,
    validated_data: dict[str, Any],
) -> Question:
    update_fields: list[str] = []
    new_content = validated_data.get("content")

    for field in ("title", "content", "category"):
        if field in validated_data:
            setattr(question, field, validated_data[field])
            update_fields.append(field)

    if update_fields:
        question.save(update_fields=update_fields)

    if new_content is not None:
        sync_question_images(question, new_content)

    return question

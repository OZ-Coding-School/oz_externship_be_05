from typing import Any

from django.db import transaction

from apps.qna.models import Question, QuestionImage


@transaction.atomic
def update_question(
    *,
    question: Question,
    validated_data: dict[str, Any],
) -> Question:

    update_fields: list[str] = []

    # 일반 필드 수정
    for field in ("title", "content", "category"):
        if field in validated_data:
            setattr(question, field, validated_data[field])
            update_fields.append(field)

    if update_fields:
        question.save(update_fields=update_fields)

    # 이미지 수정
    images_data = validated_data.get("images")
    if images_data:
        delete_ids = images_data.get("delete_ids", [])
        add_urls = images_data.get("add_urls", [])

        # 삭제
        if delete_ids:
            QuestionImage.objects.filter(
                id__in=delete_ids,
                question=question,
            ).delete()

        # 추가
        for url in add_urls:
            QuestionImage.objects.create(
                question=question,
                img_url=url,
            )

    return question

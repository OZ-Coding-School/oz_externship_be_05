from typing import Any

from apps.qna.models import Question, QuestionCategory
from apps.qna.services.question.question_image_service import sync_question_images
from apps.user.models import User


def create_question(
    *,
    author: User,
    category: QuestionCategory,
    validated_data: dict[str, Any],
) -> Question:
    question = Question.objects.create(
        author=author,
        title=validated_data["title"],
        content=validated_data["content"],
        category=category,
    )

    sync_question_images(question, validated_data["content"])

    return question

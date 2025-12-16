from typing import Any

from apps.qna.exceptions.question_exceptions import CategoryNotFoundError
from apps.qna.models import Question, QuestionCategory, QuestionImage
from apps.user.models import User


def get_category_or_raise(category_id: int) -> QuestionCategory:
    try:
        return QuestionCategory.objects.get(id=category_id)
    except QuestionCategory.DoesNotExist:
        raise CategoryNotFoundError()


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

    for url in validated_data.get("image_urls", []):
        QuestionImage.objects.create(
            question=question,
            img_url=url,
        )

    return question

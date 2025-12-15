from typing import List

from apps.qna.exceptions.question_exceptions import (
    CategoryNotFoundError,
    DuplicateQuestionTitleError,
)
from apps.qna.models import Question, QuestionCategory, QuestionImage
from apps.user.models import User


def create_question(
    *,
    author: User,
    title: str,
    content: str,
    category_id: int,
    image_urls: List[str],
) -> Question:

    # 제목 중복 검사 (도메인 규칙)
    if Question.objects.filter(title=title).exists():
        raise DuplicateQuestionTitleError()

    # 카테고리 존재 여부 검사 (도메인 규칙)
    try:
        category = QuestionCategory.objects.get(id=category_id)
    except QuestionCategory.DoesNotExist:
        raise CategoryNotFoundError()

    # Question 생성
    question = Question.objects.create(
        author=author,
        title=title,
        content=content,
        category=category,
    )

    # 이미지 생성
    for url in image_urls:
        QuestionImage.objects.create(
            question=question,
            img_url=url,
        )

    return question

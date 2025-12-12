from typing import List

from apps.qna.models import Question, QuestionCategory, QuestionImage
from apps.user.models import User


def create_question(
    *,
    author: User,
    title: str,
    content: str,
    category: QuestionCategory,
    image_urls: List[str],
) -> Question:

    question = Question.objects.create(
        author=author,
        title=title,
        content=content,
        category=category,
    )

    for url in image_urls:
        QuestionImage.objects.create(
            question=question,
            img_url=url,
        )

    return question

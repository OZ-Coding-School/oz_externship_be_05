from apps.qna.exceptions.question_exceptions import QuestionNotFoundError
from apps.qna.models import Question
from apps.qna.services.question.question_detail.selectors import get_question_detail_queryset


def get_question_detail(*, question_id: int) -> Question:
    question = get_question_detail_queryset(question_id)

    if question is None:
        raise QuestionNotFoundError()

    question.view_count += 1
    question.save(update_fields=["view_count"])

    return question

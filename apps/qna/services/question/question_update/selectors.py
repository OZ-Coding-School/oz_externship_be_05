from apps.qna.exceptions.question_exceptions import QuestionNotFoundError
from apps.qna.models import Question


# 존재 여부 판단
def get_question_for_update(*, question_id: int) -> Question:
    question = Question.objects.select_related("author").filter(id=question_id).first()

    if question is None:
        raise QuestionNotFoundError()

    return question

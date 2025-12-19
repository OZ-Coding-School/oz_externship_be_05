from django.db.models import Prefetch

from apps.qna.models import Answer, Question


# Answer / Comment 모델에 정렬코드가 있어서 따로 추가 X
def get_question_detail_queryset(question_id: int) -> Question | None:
    return (
        Question.objects.select_related("author", "category")
        .prefetch_related(
            "images",
            Prefetch(
                "answers", queryset=Answer.objects.select_related("author").prefetch_related("answer_comments__author")
            ),
        )
        .filter(id=question_id)
        .first()
    )

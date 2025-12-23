from django.db.models import Prefetch

from apps.qna.models import Answer, Question


def get_question_detail_queryset(question_id: int) -> Question | None:
    return (
        Question.objects.select_related("author", "category")
        .prefetch_related(
            "images",
            Prefetch(
                "answers",
                queryset=(
                    Answer.objects.select_related("author")
                    .prefetch_related("comments__author")
                    .order_by("-created_at")  # Answer 정렬 추가
                ),
            ),
        )
        .filter(id=question_id)
        .first()
    )

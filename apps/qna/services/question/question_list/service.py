from typing import Sequence

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, OuterRef, QuerySet, Subquery
from django.db.models.functions import Substr
from apps.qna.models import Question, QuestionImage

from .filters import (
    filter_by_answered,
    filter_by_category,
    filter_by_search,
    filter_by_sort,
)


def get_question_list(
    *,
    answer_status: str | None = None,
    category_id: int | None = None,
    search_keyword: str | None = None,
    sort: str = "latest",
) -> QuerySet[Question]:

    # base queryset
    base_qs = (
        Question.objects
        .select_related("author", "category")
        .annotate(answer_count=Count("answers", distinct=True)
    ))

    answered = None
    if answer_status == "answered":
        answered = True
    elif answer_status == "unanswered":
        answered = False

    # 필터 단계
    qs = filter_by_answered(base_qs, answered)
    qs = filter_by_category(qs, category_id)
    qs = filter_by_search(qs, search_keyword)
    qs = filter_by_sort(qs, sort)

    # annotate 단계 (가짜 컬럼들)
    return qs.annotate(
        content_preview=Substr("content", 1, 100),
        thumbnail_image_url=Subquery(
            QuestionImage.objects
            .filter(question=OuterRef("pk"))
            .order_by("created_at", "id")
            .values("img_url")[:1]
        ),
    )

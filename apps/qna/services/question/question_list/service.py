from typing import Sequence

from django.core.paginator import Paginator
from django.db.models import Count, OuterRef, QuerySet, Subquery
from django.db.models.functions import Substr

from apps.qna.exceptions.question_exceptions import QuestionListEmptyError
from apps.qna.models import Question, QuestionImage

from .filters import (
    filter_by_answered,
    filter_by_category,
    filter_by_search,
)


def get_question_list(
    *,
    answered: bool | None = None,
    category: int | None = None,
    search: str | None = None,
    page: int,
    page_size: int,
) -> tuple[Sequence[Question], dict[str, int]]:

    # base queryset
    base_qs: QuerySet[Question] = (
        Question.objects.select_related("author", "category")
        .annotate(answer_count=Count("answers", distinct=True))
        .order_by("-created_at")
    )

    # 필터 단계
    filtered_qs = filter_by_answered(base_qs, answered)
    filtered_qs = filter_by_category(filtered_qs, category)
    filtered_qs = filter_by_search(filtered_qs, search)

    # annotate 단계 (가짜 컬럼들)
    annotated_qs = filtered_qs.annotate(content_preview=Substr("content", 1, 100)).annotate(
        thumbnail_image_url=Subquery(
            QuestionImage.objects.filter(question=OuterRef("pk")).order_by("created_at").values("img_url")[:1]
        )
    )

    # pagination
    paginator = Paginator(annotated_qs, page_size)

    if paginator.count == 0:
        raise QuestionListEmptyError()

    page_obj = paginator.page(page)

    return list(page_obj.object_list), {
        "page": page,
        "page_size": page_size,
        "total_pages": paginator.num_pages,
        "total_count": paginator.count,
    }

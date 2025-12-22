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
    page: int,
    size: int,
) -> tuple[Sequence[Question], dict[str, int]]:

    # base queryset
    base_qs: QuerySet[Question] = (
        Question.objects
        .select_related("author", "category")
        .annotate(answer_count=Count("answers", distinct=True)
    ))

    answered: bool | None = None
    if answer_status == "answered":
        answered = True
    elif answer_status == "unanswered":
        answered = False

    # 필터 단계
    filtered_qs = filter_by_answered(base_qs, answered)
    filtered_qs = filter_by_category(filtered_qs, category_id)
    filtered_qs = filter_by_search(filtered_qs, search_keyword)
    filtered_qs = filter_by_sort(filtered_qs, sort)

    # annotate 단계 (가짜 컬럼들)
    annotated_qs = filtered_qs.annotate(
        content_preview=Substr("content", 1, 100),
        thumbnail_image_url=Subquery(
            QuestionImage.objects
            .filter(question=OuterRef("pk"))
            .order_by("created_at", "id")
            .values("img_url")[:1]
        ),
    )

    # pagination
    paginator = Paginator(annotated_qs, size)

    # 결과가 0건 → 예외 없이 빈 리스트 반환
    if paginator.count == 0:
        return [], {
            "page": page,
            "page_size": size,
            "total_pages": 0,
            "total_count": 0,
        }

    try:
        page_obj = paginator.page(page)
        object_list = list(page_obj.object_list)
        current_page = page
    except (EmptyPage, PageNotAnInteger):
        object_list = []
        current_page = page

    return object_list, {
        "page": current_page,
        "page_size": size,
        "total_pages": paginator.num_pages,
        "total_count": paginator.count,
    }
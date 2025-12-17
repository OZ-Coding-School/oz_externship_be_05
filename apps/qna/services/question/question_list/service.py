from django.core.paginator import Paginator
from django.db.models import BooleanField, Case, Count, OuterRef, Subquery, When, QuerySet
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
) -> tuple[QuerySet[Question], dict[str, int]]:
    qs: QuerySet[Question] = (
        Question.objects.select_related("author", "category")
        .annotate(
            answer_count=Count("answers", distinct=True),
        ) # type: ignore[misc]
        .order_by("-created_at")
    )

    qs: QuerySet[Question] = filter_by_answered(qs, answered)
    qs: QuerySet[Question] = filter_by_category(qs, category)
    qs: QuerySet[Question] = filter_by_search(qs, search)

    qs: QuerySet[Question] = qs.annotate(content_preview=Substr("content", 1, 100)) # type: ignore[misc]

    thumbnail_subquery = (
        QuestionImage.objects.filter(question=OuterRef("pk")).order_by("created_at").values("img_url")[:1]
    )
    qs: QuerySet[Question] = qs.annotate(thumbnail_image_url=Subquery(thumbnail_subquery)) # type: ignore[misc]

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    if paginator.count == 0:
        raise QuestionListEmptyError()

    return page_obj.object_list, {
        "page": page,
        "page_size": page_size,
        "total_pages": paginator.num_pages,
        "total_count": paginator.count,
    }

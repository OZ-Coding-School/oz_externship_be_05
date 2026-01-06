from django.db.models import Q, QuerySet

from apps.qna.models import Question
from apps.qna.services.question.question_list.category_utils import (
    get_descendant_category_ids,
)


def filter_by_answered(
    qs: QuerySet[Question],
    answered: bool | None,
) -> QuerySet[Question]:
    if answered is True:
        return qs.filter(answer_count__gt=0)  # type: ignore[misc]
    if answered is False:
        return qs.filter(answer_count=0)  # type: ignore[misc]
    return qs


def filter_by_category(
    qs: QuerySet[Question],
    category_id: int | None,
) -> QuerySet[Question]:
    if category_id is None:
        return qs

    category_ids = get_descendant_category_ids(category_id)
    return qs.filter(category_id__in=category_ids)


def filter_by_search(
    qs: QuerySet[Question],
    search: str | None,
) -> QuerySet[Question]:
    if not search:
        return qs

    return qs.filter(Q(title__icontains=search) | Q(content__icontains=search))


def filter_by_sort(
    qs: QuerySet[Question],
    sort: str,
) -> QuerySet[Question]:
    if sort == "latest":
        return qs.order_by("-created_at", "-id")

    if sort == "oldest":
        return qs.order_by("created_at", "id")

    if sort == "views":
        return qs.order_by("-view_count", "-id")

    return qs

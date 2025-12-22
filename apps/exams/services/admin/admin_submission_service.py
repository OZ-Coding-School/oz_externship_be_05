from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional

from django.db.models import Q, QuerySet
from rest_framework.exceptions import NotFound, ValidationError

from apps.exams.models import ExamSubmission

Order = Literal["asc", "desc"]


@dataclass(frozen=True)
class AdminSubmissionListParams:
    page: int = 1
    size: int = 10
    search_keyword: str = ""
    cohort_id: Optional[int] = None
    exam_id: Optional[int] = None
    sort: str = "finished_at"
    order: Order = "desc"


ALLOWED_SORTS: dict[str, str] = {
    "score": "score",
    "started_at": "started_at",
    "finished_at": "created_at",
    "cheating_count": "cheating_count",
    "name": "submitter__name",
    "nickname": "submitter__nickname",
}


def _bad_request() -> ValidationError:
    return ValidationError({"error_detail": "유효하지 않은 요청입니다."})


def _not_found() -> NotFound:
    return NotFound({"error_detail": "조회된 응시 내역이 없습니다."})


def _validate_params(params: AdminSubmissionListParams) -> None:
    if params.page < 1:
        raise _bad_request()
    if params.size < 1 or params.size > 100:
        raise _bad_request()
    if params.sort not in ALLOWED_SORTS:
        raise _bad_request()
    if params.order not in ("asc", "desc"):
        raise _bad_request()


def _apply_filters(qs: QuerySet[ExamSubmission], params: AdminSubmissionListParams) -> QuerySet[ExamSubmission]:
    if params.cohort_id is not None:
        qs = qs.filter(deployment__cohort_id=params.cohort_id)

    if params.exam_id is not None:
        qs = qs.filter(deployment__exam_id=params.exam_id)

    if params.search_keyword:
        kw = params.search_keyword.strip()
        qs = qs.filter(Q(submitter__nickname__icontains=kw) | Q(submitter__name__icontains=kw))

    return qs


def _apply_sort(qs: QuerySet[ExamSubmission], params: AdminSubmissionListParams) -> QuerySet[ExamSubmission]:
    field = ALLOWED_SORTS[params.sort]
    prefix = "" if params.order == "asc" else "-"
    return qs.order_by(f"{prefix}{field}", f"{prefix}id")


def get_admin_exam_submission_list(params: AdminSubmissionListParams) -> dict[str, Any]:
    _validate_params(params)

    qs = ExamSubmission.objects.all().select_related(
        "submitter",
        "deployment",
        "deployment__cohort",
        "deployment__exam",
        "deployment__exam__subject",
        "deployment__cohort__course",
    )

    qs = _apply_filters(qs, params)
    total_count = qs.count()
    if total_count == 0:
        raise _not_found()

    qs = _apply_sort(qs, params)

    offset = (params.page - 1) * params.size
    page_items = list(qs[offset : offset + params.size])
    if not page_items:
        raise _not_found()

    return {
        "page": params.page,
        "size": params.size,
        "total_count": total_count,
        "submissions": page_items,
    }

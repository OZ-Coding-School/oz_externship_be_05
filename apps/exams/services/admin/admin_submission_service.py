from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional

from django.db.models import Q, QuerySet
from rest_framework.exceptions import NotFound, ValidationError

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models import ExamSubmission

ALLOWED_SORTS: dict[str, str] = {
    "score": "score",
    "started_at": "started_at",
    "finished_at": "created_at",
    "cheating_count": "cheating_count",
    "name": "submitter__name",
    "nickname": "submitter__nickname",
}

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


def _bad_request() -> ValidationError:
    return ValidationError(EMS.E400_INVALID_REQUEST("조회"))


def _not_found() -> NotFound:
    return NotFound(EMS.E404_NO_EXAM_HISTORY)


def _validate_params(params: AdminSubmissionListParams) -> None:
    validators = {
        "page": params.page >= 1,
        "size": 1 <= params.size <= 100,
        "sort": params.sort in ALLOWED_SORTS,
        "order": params.order in ("asc", "desc"),
    }
    if not all(validators.values()):
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
    if not field:
        raise _bad_request()

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

    start = (params.page - 1) * params.size
    end = start + params.size
    submissions = list(qs[start:end])

    return {
        "page": params.page,
        "size": params.size,
        "total_count": total_count,
        "submissions": submissions,
    }

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, Optional, cast

from django.db.models import Q, QuerySet
from rest_framework.exceptions import NotFound, ValidationError

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models import ExamSubmission

Order = Literal["asc", "desc"]

ALLOWED_SORTS: dict[str, str] = {
    "score": "score",
    "started_at": "started_at",
    "finished_at": "created_at",
    "cheating_count": "cheating_count",
    "name": "submitter__name",
    "nickname": "submitter__nickname",
}


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
    # "유효하지 않은 조회 요청입니다."
    return ValidationError(EMS.E400_INVALID_REQUEST("조회"))


def parse_admin_submission_list_params(qp: Mapping[str, str]) -> AdminSubmissionListParams:
    try:
        page = int(qp.get("page", 1))
        size = int(qp.get("size", 10))
        search_keyword = str(qp.get("search_keyword", "") or "")
        cohort_id = int(qp.get("cohort_id", 0)) if qp.get("cohort_id") else None
        exam_id = int(qp.get("exam_id", 0)) if qp.get("exam_id") else None
        sort = qp.get("sort", "finished_at")
        order = qp.get("order", "desc")
    except (TypeError, ValueError, KeyError):
        raise _bad_request()

    params = AdminSubmissionListParams(
        page=page,
        size=size,
        search_keyword=search_keyword,
        cohort_id=cohort_id,
        exam_id=exam_id,
        sort=sort,
        order=cast(Order, order),
    )
    _validate_params(params)
    return params


def _validate_params(params: AdminSubmissionListParams) -> None:
    validators = {
        "page": params.page >= 1,
        "size": 1 <= params.size <= 100,
        "sort": params.sort in ALLOWED_SORTS,
        "order": params.order in ("asc", "desc"),
    }
    if not all(validators.values()):
        raise _bad_request()


def build_admin_submission_query(params: AdminSubmissionListParams) -> QuerySet[ExamSubmission]:
    qs = ExamSubmission.objects.all().select_related(
        "submitter",
        "deployment",
        "deployment__cohort",
        "deployment__cohort__course",
        "deployment__exam",
        "deployment__exam__subject",
    )

    if params.cohort_id is not None:
        qs = qs.filter(deployment__cohort_id=params.cohort_id)

    if params.exam_id is not None:
        qs = qs.filter(deployment__exam_id=params.exam_id)

    keyword = params.search_keyword.strip()
    if keyword:
        qs = qs.filter(Q(submitter__nickname__icontains=keyword) | Q(submitter__name__icontains=keyword))

    sort_field = ALLOWED_SORTS[params.sort]
    prefix = "-" if params.order == "desc" else ""
    return qs.order_by(f"{prefix}{sort_field}", f"{prefix}id")

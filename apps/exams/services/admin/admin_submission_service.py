from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional

from django.db.models import Q, QuerySet
from rest_framework.exceptions import NotFound, ValidationError

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models import ExamSubmission

Order = Literal["asc", "desc"]

# sort 파라미터(클라이언트) -> 실제 DB 필드 매핑
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


def _not_found() -> NotFound:
    return NotFound(EMS.E404_NO_EXAM_HISTORY)


def _validate_params(params: AdminSubmissionListParams) -> None:
    # 서비스가 요청 검증 책임 (뷰는 파싱만)
    if params.page < 1:
        raise _bad_request()

    if params.size < 1 or params.size > 100:
        raise _bad_request()

    # sort는 정렬 필드 매핑이 정의된 것만 허용
    if params.sort not in ALLOWED_SORTS:
        raise _bad_request()

    # order는 asc/desc만 허용
    if params.order not in ("asc", "desc"):
        raise _bad_request()


def _apply_filters(qs: QuerySet[ExamSubmission], params: AdminSubmissionListParams) -> QuerySet[ExamSubmission]:
    if params.cohort_id is not None:
        qs = qs.filter(deployment__cohort_id=params.cohort_id)

    if params.exam_id is not None:
        qs = qs.filter(deployment__exam_id=params.exam_id)

    keyword = params.search_keyword.strip()
    if keyword:
        qs = qs.filter(Q(submitter__nickname__icontains=keyword) | Q(submitter__name__icontains=keyword))

    return qs


def _apply_sort(qs: QuerySet[ExamSubmission], params: AdminSubmissionListParams) -> QuerySet[ExamSubmission]:
    # 여기서는 추가 검증하지 않음 (_validate_params에서 이미 보장)
    field = ALLOWED_SORTS[params.sort]
    prefix = "" if params.order == "asc" else "-"

    # 동점일 때 결과가 흔들리지 않도록 id로 2차 정렬
    return qs.order_by(f"{prefix}{field}", f"{prefix}id")


def get_admin_exam_submission_list(params: AdminSubmissionListParams) -> dict[str, Any]:
    _validate_params(params)

    qs = ExamSubmission.objects.all().select_related(
        "submitter",
        "deployment",
        "deployment__cohort",
        "deployment__cohort__course",
        "deployment__exam",
        "deployment__exam__subject",
    )

    qs = _apply_filters(qs, params)

    total_count = qs.count()
    if total_count == 0:
        raise _not_found()

    qs = _apply_sort(qs, params)

    start = (params.page - 1) * params.size
    end = start + params.size

    return {
        "page": params.page,
        "size": params.size,
        "total_count": total_count,
        "submissions": list(qs[start:end]),
    }

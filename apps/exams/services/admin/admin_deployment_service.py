import random
import string
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.db.models import Avg, Count, QuerySet
from rest_framework.exceptions import ValidationError

from apps.courses.models import Cohort

# from apps.courses.models import CohortStudent
from apps.exams.models import Exam, ExamDeployment, ExamQuestion, ExamSubmission
from apps.exams.models.exam_deployment import DeploymentStatus
from apps.exams.services.admin.validators.deployment_validator import (
    DeploymentValidator,
)


# 시험 배포 목록 조회 -------------------------------------------------------
def list_admin_deployments(
    *,
    cohort: Optional[Cohort] = None,
    status: Optional[str] = None,
    search_keyword: Optional[str] = None,
    sort: str = "created_at",
    order: str = "desc",
) -> QuerySet[ExamDeployment]:

    qs: QuerySet[ExamDeployment] = ExamDeployment.objects.select_related("cohort", "exam").annotate(
        participant_count=Count("submissions", distinct=True),
        avg_score=Avg("submissions__score"),
    )

    # 필터링(과정별, 기수별)
    if cohort is not None:
        qs = qs.filter(cohort=cohort)

    if status is not None:
        if status not in DeploymentStatus.values:
            raise ValidationError({"status": "유효하지 않은 배포 상태입니다."})
        qs = qs.filter(status=status)

    # 검색(검색 키워드와 일부 또는 완전 일치)
    if search_keyword:
        qs = qs.filter(
            exam__title__icontains=search_keyword,
        )

    # 정렬(최신순, 응시횟수 많은 순, 평균 점수 높은 순)
    sort_map = {
        "created_at": "created_at",
        "participant_count": "participant_count",
        "avg_score": "avg_score",
    }

    sort_field = sort_map.get(sort, "created_at")
    prefix = "-" if order == "desc" else ""

    return qs.order_by(f"{prefix}{sort_field}")


# 단일 시험 배포 상세 조회 ---------------------------------------------------
def get_admin_deployment_detail(*, deployment_id: int) -> ExamDeployment:
    try:
        deployment = ExamDeployment.objects.select_related(
            "exam",
            "cohort",
            "exam__subject",
        ).get(pk=deployment_id)
    except ExamDeployment.DoesNotExist as exc:
        raise ValidationError({"deployment_id": "해당 배포 정보를 찾을 수 없습니다."}) from exc

    # 시험 문항 조회
    questions = ExamQuestion.objects.filter(exam=deployment.exam).values(
        "id",
        "type",
        "question",
        "point",
    )
    #
    # # 응시 대상자 수
    # total_target_count = CohortStudent.objects.filter(cohort_id=deployment.cohort.id).count()
    #
    # # 응시자 수
    # submit_count = ExamSubmission.objects.filter(deployment=deployment).count()
    #
    # # 미응시자 수
    # not_submitted_count = max(total_target_count - submit_count, 0)
    #
    # setattr(deployment, "questions", list(questions))
    # setattr(deployment, "submit_count", submit_count)
    # setattr(deployment, "not_submitted_count", not_submitted_count)

    return deployment


# 새 시험 배포 생성 --------------------------------------------------------
@transaction.atomic
def create_deployment(
    *,
    cohort: Cohort,
    exam: Exam,
    duration_time: int,
    open_at: datetime,
    close_at: datetime,
) -> ExamDeployment:

    return ExamDeployment.objects.create(
        cohort=cohort,
        exam=exam,
        duration_time=duration_time,
        access_code=_generate_base62_code(),
        open_at=open_at,
        close_at=close_at,
        status=DeploymentStatus.ACTIVATED,
        questions_snapshot=_build_questions_snapshot(exam),
    )


# 시험 배포 정보 수정 (open_at, close_at, duration_time) -------------------------
# TODO: API명세에는 배포 수정이 없음. 근데 있는 편이 유리하지 않나? 물어보기
@transaction.atomic
def update_deployment(
    *,
    deployment: ExamDeployment,
    data: Dict[str, Any],
) -> ExamDeployment:

    DeploymentValidator.validate_not_started(
        open_at=deployment.open_at,
        status=deployment.status,
    )

    allowed_fields = {"open_at", "close_at", "duration_time"}

    for field, value in data.items():
        if field not in allowed_fields:
            raise ValidationError({"field": "수정할 수 없는 필드입니다."})
        setattr(deployment, field, value)

    deployment.save(update_fields=list(data.keys()) + ["updated_at"])
    return deployment


# 시험 배포 상태 on/off (activated / deactivated) --------------------------
@transaction.atomic
def set_deployment_status(
    *,
    deployment: ExamDeployment,
    status: str,
) -> ExamDeployment:

    if status not in DeploymentStatus.values:
        raise ValidationError({"status": "유효하지 않은 배포 상태입니다."})

    # 비활성화시 응시 중인 시험은 즉시 종료되어야 함
    if deployment.status == DeploymentStatus.ACTIVATED and status == DeploymentStatus.DEACTIVATED:
        pass

    deployment.status = status
    deployment.save(update_fields=["status", "updated_at"])
    return deployment


# 시험 배포 삭제 ---------------------------------------------------------
@transaction.atomic
def delete_deployment(*, deployment: ExamDeployment) -> None:

    DeploymentValidator.validate_not_started(
        open_at=deployment.open_at,
        status=deployment.status,
    )

    # 응시 내역이 존재하면 삭제 불가
    if ExamSubmission.objects.filter(deployment=deployment).exists():
        raise ValidationError({"deployment": "응시 내역이 있는 시험 배포는 삭제할 수 없습니다."})

    deployment.delete()


# ExamQuestion 목록을 기반으로 배포용 문항 스냅샷 생성 --------------------------
# 어드민용
def _build_questions_snapshot(exam: Exam) -> List[Dict[str, Any]]:
    questions: QuerySet[ExamQuestion] = ExamQuestion.objects.filter(exam=exam).order_by("id")

    return [
        {
            "id": q.id,
            "question": q.question,
            "prompt": q.prompt,
            "blank_count": q.blank_count,
            "options": q.options,
            "type": q.type,
            "answer": q.answer,
            "point": q.point,
            "explanation": q.explanation,
        }
        for q in questions
    ]


# Base62 코드 생성 --------------------------------------------------------
def _generate_base62_code(length: int = 8) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

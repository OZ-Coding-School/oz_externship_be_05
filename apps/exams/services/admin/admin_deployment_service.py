import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.db.models import Avg, Count, FloatField, QuerySet, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.core.utils.base62 import Base62
from apps.courses.models import Cohort
from apps.exams.constants import DEFAULT_DEPLOYMENT_SORT, DEPLOYMENT_SORT_OPTIONS
from apps.exams.exceptions import DeploymentConflictException
from apps.exams.models import Exam, ExamDeployment, ExamQuestion
from apps.exams.models.exam_deployment import DeploymentStatus
from apps.exams.services.admin.validators.deployment_validator import (
    DeploymentValidator,
)


# 시험 배포 목록 조회 -------------------------------------------------------
def list_admin_deployments(
    *,
    cohort_id: Optional[int] = None,
    cohort: Optional[Cohort] = None,
    subject_id: Optional[int] = None,
    search_keyword: Optional[str] = None,
    sort: str = "created_at",
    order: str = "desc",
) -> QuerySet[ExamDeployment]:

    qs: QuerySet[ExamDeployment] = ExamDeployment.objects.select_related(
        "exam", "exam__subject", "cohort", "cohort__course"
    ).annotate(
        submit_count=Count("submissions", distinct=True),
        avg_score=Coalesce(
            Avg("submissions__score"),
            Value(0.0),
            output_field=FloatField(),
        ),
    )

    # 기수 필터
    if cohort is not None:
        qs = qs.filter(cohort=cohort)
    elif cohort_id is not None:
        qs = qs.filter(cohort_id=cohort_id)

    # 과목 필터
    if subject_id is not None:
        qs = qs.filter(exam__subject_id=subject_id)

    # 검색 (시험명)
    if search_keyword:
        qs = qs.filter(exam__title__icontains=search_keyword)

    # 정렬(최신순, 응시횟수 많은 순, 평균 점수 높은 순)
    if sort not in DEPLOYMENT_SORT_OPTIONS.values():
        sort = DEFAULT_DEPLOYMENT_SORT

    prefix = "-" if order == "desc" else ""

    return qs.order_by(f"{prefix}{sort}")


# 단일 시험 배포 상세 조회 ---------------------------------------------------
def get_admin_deployment_detail(*, deployment_id: int) -> ExamDeployment:
    try:
        deployment = (
            ExamDeployment.objects.select_related(
                "exam",
                "exam__subject",
                "cohort",
                "cohort__course",
            )
            .annotate(
                submit_count=Count("submissions__submitter", distinct=True),
                total_target_count=Count("cohort__cohortstudent", distinct=True),
            )
            .get(pk=deployment_id)
        )

    except ExamDeployment.DoesNotExist as exc:
        raise NotFound(detail={"deployment_id": "해당 배포 정보를 찾을 수 없습니다."}) from exc

    return deployment


# 새 시험 배포 생성 --------------------------------------------------------
@transaction.atomic
def create_deployment(
    *, cohort: Cohort, exam: Exam, duration_time: int, open_at: datetime, close_at: datetime
) -> ExamDeployment:
    """
    배포 생성
    성공: ExamDeployment 반환
    실패: 409
    """

    now = timezone.now()

    # 중복 배포 확인
    if ExamDeployment.objects.filter(cohort=cohort, exam=exam).exists():
        raise DeploymentConflictException(
            detail=f"동일한 조건의 배포가 이미 존재합니다: '{exam.title}' - {cohort.number}기 "
        )

    # 이미 해당 기수에 활성화된 배포내역이 있는지 확인
    active_deployments = ExamDeployment.objects.filter(cohort=cohort, exam=exam, status=DeploymentStatus.ACTIVATED)
    for dep in active_deployments:
        if dep.open_at <= now:
            raise DeploymentConflictException(detail=f"이미 활성화된 시험입니다: '{exam.title}' - {cohort.number}기")

    # 정상 생성
    deployment = ExamDeployment.objects.create(
        cohort=cohort,
        exam=exam,
        duration_time=duration_time,
        open_at=open_at,
        close_at=close_at,
        access_code=Base62.uuid_encode(uuid.uuid4(), length=6),
        status=DeploymentStatus.ACTIVATED,
        questions_snapshot=_build_questions_snapshot(exam),
    )
    return deployment


# 시험 배포 정보 수정 (open_at, close_at, duration_time) -------------------------
@transaction.atomic
def update_deployment(*, deployment: ExamDeployment, data: Dict[str, Any]) -> ExamDeployment:

    # 시작된 시험 수정 불가
    DeploymentValidator.validate_not_started(
        open_at=deployment.open_at,
        status=deployment.status,
    )

    # 종료된 시험 수정 불가
    DeploymentValidator.validate_not_finished(
        close_at=deployment.close_at,
        status=deployment.status,
    )

    for field, value in data.items():
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

    # 종료된 시험 상태 변경 불가
    DeploymentValidator.validate_not_finished(
        close_at=deployment.close_at,
        status=deployment.status,
    )

    # 비활성화시 응시 중인 시험은 즉시 종료되어야 함
    if deployment.status == DeploymentStatus.ACTIVATED and status == DeploymentStatus.DEACTIVATED:
        pass

    deployment.status = status
    deployment.save(update_fields=["status", "updated_at"])
    return deployment


# 시험 배포 삭제 ---------------------------------------------------------
@transaction.atomic
def delete_deployment(*, deployment: ExamDeployment) -> None:

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

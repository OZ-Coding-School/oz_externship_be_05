import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.courses.models import Cohort
from apps.exams.models import Exam, ExamDeployment, ExamQuestion, ExamSubmission
from apps.exams.models.exam_deployment import DeploymentStatus
from apps.exams.services.admin.validators.deployment_validator import (
    DeploymentValidator,
)


# validation helpers ---------------------------------------------------------
def _validate_create(*, open_at: datetime, close_at: datetime) -> None:
    DeploymentValidator.validate_open(open_at)
    DeploymentValidator.validate_time(open_at, close_at)


def _validate_update_deployment(*, deployment: ExamDeployment, data: Dict[str, Any]) -> None:
    if "open_at" in data:
        new_open_at = data["open_at"]
        if new_open_at != deployment.open_at:
            DeploymentValidator.validate_not_started(deployment.open_at)
            DeploymentValidator.validate_time(new_open_at, deployment.close_at)

        if "open_at" in data and "close_at" in data:
            DeploymentValidator.validate_time(data["open_at"], data["close_at"])


def _validate_status_change(*, deployment: ExamDeployment) -> None:
    DeploymentValidator.validate_not_closed(deployment.close_at)


def _validate_delete(*, deployment: ExamDeployment) -> None:
    DeploymentValidator.validate_not_started(deployment.open_at)


def _validate_exam_and_cohort(*, exam: Exam, cohort: Cohort) -> None:
    if exam.subject.course_id != cohort.course_id:
        raise ValidationError({"cohort": "시험(exam)과 기수(cohort)의 과정(course)이 일치하지 않습니다."})


# ExamQuestion 목록을 기반으로 배포용 문항 스냅샷 생성 ---------------------------------------------------------
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


# 시험 배포 목록 조회 ---------------------------------------------------------
def list_deployments(
    *,
    cohort: Optional[Cohort] = None,
    status: Optional[str] = None,
) -> QuerySet[ExamDeployment]:

    qs: QuerySet[ExamDeployment] = ExamDeployment.objects.select_related("cohort", "exam").order_by("-created_at")

    if cohort is not None:
        qs = qs.filter(cohort=cohort)

    if status is not None:
        qs = qs.filter(status=status)

    return qs


# 단일 시험 배포 상세 조회 ---------------------------------------------------------
def get_deployment(*, deployment_id: int) -> ExamDeployment:
    try:
        return ExamDeployment.objects.select_related("cohort", "exam").get(pk=deployment_id)
    except ExamDeployment.DoesNotExist as exc:
        raise ValidationError({"deployment_id": "존재하지 않는 시험 배포입니다."}) from exc


# 새 시험 배포 생성 ---------------------------------------------------------
@transaction.atomic
def create_deployment(
    *,
    cohort: Cohort,
    exam: Exam,
    duration_time: int,
    open_at: datetime,
    close_at: datetime,
) -> ExamDeployment:

    _validate_create(open_at=open_at, close_at=close_at)
    _validate_exam_and_cohort(exam=exam, cohort=cohort)

    return ExamDeployment.objects.create(
        cohort=cohort,
        exam=exam,
        duration_time=duration_time,
        access_code=str(uuid.uuid4())[:8],
        open_at=open_at,
        close_at=close_at,
        status=DeploymentStatus.ACTIVATED,
        questions_snapshot=_build_questions_snapshot(exam),
    )


# 시험 배포 정보 수정 (부분 수정 포함) ---------------------------------------------------------
@transaction.atomic
def update_deployment(
    *,
    deployment: ExamDeployment,
    data: Dict[str, Any],
) -> ExamDeployment:

    _validate_update_deployment(deployment=deployment, data=data)

    for field, value in data.items():
        setattr(deployment, field, value)

    deployment.save(update_fields=list(data.keys()) + ["updated_at"])
    return deployment


# 시험 배포 상태 on/off (activated / deactivated) ---------------------------------------------------------
@transaction.atomic
def set_deployment_status(
    *,
    deployment: ExamDeployment,
    status: str,
) -> ExamDeployment:

    if status not in DeploymentStatus.values:
        raise ValidationError({"status": "유효하지 않은 배포 상태입니다."})

    _validate_status_change(deployment=deployment)

    deployment.status = status
    deployment.save(update_fields=["status", "updated_at"])
    return deployment


# 시험 배포 삭제 ---------------------------------------------------------
@transaction.atomic
def delete_deployment(*, deployment: ExamDeployment) -> None:

    _validate_delete(deployment=deployment)

    # 응시 내역이 존재하면 삭제 불가
    if ExamSubmission.objects.filter(deployment=deployment).exists():
        raise ValidationError({"deployment": "응시 내역이 있는 시험 배포는 삭제할 수 없습니다."})

    deployment.delete()

from datetime import datetime
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.courses.models import Cohort
from apps.exams.models import Exam, ExamDeployment, ExamQuestion, ExamSubmission
from apps.exams.models.exam_deployment import DeploymentStatus


# 시험 배포 목록 조회
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


# 단일 시험 배포 상세 조회
def get_deployment(*, deployment_id: int) -> ExamDeployment:
    try:
        return ExamDeployment.objects.select_related("cohort", "exam").get(pk=deployment_id)
    except ExamDeployment.DoesNotExist as exc:
        raise ValidationError("존재하지 않는 시험 배포입니다.") from exc


# ExamQuestion 목록을 기반으로 배포용 문항 스냅샷 생성
def _build_questions_snapshot(exam: Exam) -> List[Dict[str, Any]]:
    questions: QuerySet[ExamQuestion] = ExamQuestion.objects.filter(exam=exam).order_by("id")

    snapshot: List[Dict[str, Any]] = []
    for q in questions:
        snapshot.append(
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
        )
    return snapshot


# exam과 cohort가 같은 course에 속하는지 검증
def _validate_exam_and_cohort(course_exam: Exam, cohort: Cohort) -> None:
    if course_exam.subject.course_id != cohort.course_id:
        raise ValidationError("시험(exam), 기수(cohort)의 과정(course) 정보가 일치하지 않습니다.")


# 새 시험 배포 생성
@transaction.atomic
def create_deployment(
    *,
    cohort: Cohort,
    exam: Exam,
    duration_time: int,
    access_code: str,
    open_at: datetime,
    close_at: datetime,
) -> ExamDeployment:

    # 시간 검증: 생성 시 open_at 은 현재보다 이후여야 함
    if open_at <= timezone.now():
        raise ValidationError("시험 시작 시간(open_at)은 현재 시각 이후여야 합니다.")

    if open_at >= close_at:
        raise ValidationError("시험 시작 시간(open_at)은 종료 시간(close_at)보다 빨라야 합니다.")

    # cohort / exam - course 매칭 검증
    _validate_exam_and_cohort(exam, cohort)

    # 문항 스냅샷 생성
    questions_snapshot: List[Dict[str, Any]] = _build_questions_snapshot(exam)

    deployment: ExamDeployment = ExamDeployment.objects.create(
        cohort=cohort,
        exam=exam,
        duration_time=duration_time,
        access_code=access_code,
        open_at=open_at,
        close_at=close_at,
        status=DeploymentStatus.ACTIVATED,
        questions_snapshot=questions_snapshot,
    )
    return deployment


# 시험 배포 정보 수정 (부분 수정 포함)
@transaction.atomic
def update_deployment(
    *,
    deployment: ExamDeployment,
    data: Dict[str, Any],
) -> ExamDeployment:

    # 이미 시작된 배포의 open_at 을 과거/다른 값으로 변경하려는 경우 차단
    if "open_at" in data:
        new_open_at = data["open_at"]
        if deployment.open_at <= timezone.now() and new_open_at != deployment.open_at:
            raise ValidationError("이미 시작된 시험의 시작 시간은 수정할 수 없습니다.")

        if "close_at" not in data:
            # close_at 이 그대로일 때는 새 open_at 과의 순서만 다시 확인
            if new_open_at >= deployment.close_at:
                raise ValidationError("시험 시작 시간(open_at)은 종료 시간(close_at)보다 빨라야 합니다.")

    # open_at/close_at 둘 다 들어온 경우 일관성 재검증
    if "open_at" in data and "close_at" in data:
        if data["open_at"] >= data["close_at"]:
            raise ValidationError("시험 시작 시간(open_at)은 종료 시간(close_at)보다 빨라야 합니다.")

    for field, value in data.items():
        setattr(deployment, field, value)

    deployment.save(update_fields=list(data.keys()) + ["updated_at"])
    return deployment


# 시험 배포 상태 on/off (activated / deactivated)
@transaction.atomic
def set_deployment_status(
    *,
    deployment: ExamDeployment,
    status: str,
) -> ExamDeployment:

    if status not in DeploymentStatus.values:
        raise ValidationError("유효하지 않은 배포 상태입니다.")

    # 이미 종료된 시험은 상태 변경 불가
    if deployment.close_at <= timezone.now():
        raise ValidationError("종료된 시험의 상태는 변경할 수 없습니다.")

    deployment.status = status
    deployment.save(update_fields=["status", "updated_at"])
    return deployment


# 시험 배포 삭제
@transaction.atomic
def delete_deployment(*, deployment: ExamDeployment) -> None:

    # 이미 시작된 배포는 삭제 불가
    if deployment.open_at <= timezone.now():
        raise ValidationError("이미 시작된 시험 배포는 삭제할 수 없습니다.")

    # 응시 내역이 존재하면 삭제 불가
    has_submissions: bool = ExamSubmission.objects.filter(deployment=deployment).exists()
    if has_submissions:
        raise ValidationError("응시 내역이 있는 시험 배포는 삭제할 수 없습니다.")

    deployment.delete()

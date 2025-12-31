from typing import Any, Dict, Optional

from django.db.models import Prefetch, QuerySet
from django.utils import timezone

from apps.exams.models import DeploymentStatus, ExamDeployment, ExamSubmission
from apps.exams.models.exam_deployment import DeploymentStatus
from apps.user.models.role import CohortStudent


def get_student_exam_status(deployment: ExamDeployment) -> Dict[str, Any]:
    """
    학생용 시험 상태 판단
    """
    now = timezone.now()

    # 비활성화, 종료, 오픈 전
    is_not_active = deployment.status != DeploymentStatus.ACTIVATED
    is_time_over = deployment.close_at and now > deployment.close_at
    is_not_opened = deployment.open_at and now < deployment.open_at

    if is_not_active or is_time_over or is_not_opened:
        return {"exam_status": DeploymentStatus.DEACTIVATED, "force_submit": True}

    # 정상
    return {"exam_status": DeploymentStatus.ACTIVATED, "force_submit": False}


def get_exam_deployment_queryset(user: Any, filter_status: Optional[str] = None) -> QuerySet[ExamDeployment]:
    """
    쪽지시험 상태
    """
    # 기수 정보 확인
    user_cohort_ids = CohortStudent.objects.filter(user=user).values_list("cohort_id", flat=True)
    if not user_cohort_ids:
        # 빈 쿼리셋 반환
        return ExamDeployment.objects.none()

    # 해당 기수 & 활성화 상태
    queryset = ExamDeployment.objects.filter(
        cohort_id__in=user_cohort_ids, status=DeploymentStatus.ACTIVATED
    ).select_related("exam", "exam__subject")

    # 상태별 필터링
    if filter_status == "done":
        queryset = queryset.filter(submissions__submitter=user)
    elif filter_status == "pending":
        queryset = queryset.exclude(submissions__submitter=user)

    # 최적화 및 정렬
    user_submissions = ExamSubmission.objects.filter(submitter=user)
    return (
        queryset.prefetch_related(Prefetch("submissions", queryset=user_submissions, to_attr="user_submission_list"))
        .distinct()
        .order_by("-created_at")
    )

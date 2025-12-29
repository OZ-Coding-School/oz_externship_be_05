from typing import Any, Dict

from django.utils import timezone

from apps.exams.models import ExamDeployment
from apps.exams.models.exam_deployment import DeploymentStatus


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

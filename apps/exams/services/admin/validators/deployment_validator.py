from datetime import datetime

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.exams.exceptions import DeploymentConflictException
from apps.exams.models.exam_deployment import DeploymentStatus


# 시험 배포 시간 검증
class DeploymentValidator:

    @staticmethod
    def _now() -> datetime:
        return timezone.now()

    # open_at < close_at
    @staticmethod
    def validate_time(open_at: datetime, close_at: datetime) -> None:
        if open_at >= close_at:
            raise ValidationError({"open_at": "시험 시작 시간(open_at)은 종료 시간(close_at)보다 빨라야 합니다."})

    # 과거 배포 금지
    @staticmethod
    def validate_open(open_at: datetime) -> None:
        if open_at <= DeploymentValidator._now():
            raise ValidationError({"open_at": "시험 시작 시간(open_at)은 현재 시각 이후여야 합니다."})

    # 상태 기반 규칙 - 시작된 시험의 시간 변경 불가
    @staticmethod
    def validate_not_started(*, open_at: datetime, status: str) -> None:
        if open_at <= DeploymentValidator._now() and status == DeploymentStatus.ACTIVATED:
            raise ValidationError({"open_at": "이미 시작된 시험의 시작 시간은 수정/삭제할 수 없습니다."})

    # 상태 기반 규칙 - 종료된 시험 변경 불가
    @staticmethod
    def validate_not_finished(*, close_at: datetime, status: str) -> None:
        if close_at <= DeploymentValidator._now() and status == DeploymentStatus.DEACTIVATED:
            raise ValidationError({"status": "종료된 시험은 변경할 수 없습니다."})

    # 상태 기반 규칙 - 충돌 검증
    @staticmethod
    def validate_status_conflict(current_status: str, requested_status: str) -> None:
        if current_status == requested_status:
            raise DeploymentConflictException(detail=f"해당 배포는 이미 {requested_status} 상태입니다.")

from datetime import datetime

from rest_framework.exceptions import ValidationError


# 시험 배포 시간 검증 (open_at < close_at)
class DeploymentValidator:
    @staticmethod
    def validate_time(open_at: datetime, close_at: datetime) -> None:
        if open_at >= close_at:
            raise ValidationError("open_at must be earlier than close_at")

from typing import Any, Dict

from rest_framework import serializers

from apps.exams.models import ExamDeployment
from apps.exams.services.admin.validators.deployment_validator import (
    DeploymentValidator,
)


# 시험 배포 데이터 검증
class AdminDeploymentSerializer(serializers.ModelSerializer[ExamDeployment]):
    class Meta:
        model = ExamDeployment
        fields = [
            "id",
            "cohort",
            "exam",
            "duration_time",
            "access_code",
            "open_at",
            "close_at",
            "status",
        ]
        read_only_fields = ("id",)

    # 시간 검증 (open_at < close_at)
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        DeploymentValidator.validate_time(attrs["open_at"], attrs["close_at"])
        return attrs

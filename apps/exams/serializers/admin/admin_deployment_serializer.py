from typing import Any, Dict

from rest_framework import serializers

from apps.exams.models import ExamDeployment
from apps.exams.models.exam_deployment import DeploymentStatus
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
        read_only_fields = ("id", "access_code")

    # 시간 검증
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:

        # create / update 구분
        instance = self.instance

        open_at = attrs.get("open_at", getattr(instance, "open_at", None))
        close_at = attrs.get("close_at", getattr(instance, "close_at", None))

        # open_at < close_at
        if open_at and close_at:
            DeploymentValidator.validate_time(open_at, close_at)

        # create 일 경우
        if instance is None and open_at is not None:
            DeploymentValidator.validate_open(open_at)

        # exam - cohort 관계 검증
        exam = attrs.get("exam", getattr(instance, "exam", None))
        cohort = attrs.get("cohort", getattr(instance, "cohort", None))
        if exam and cohort and exam.subject.course_id != cohort.course_id:
            raise serializers.ValidationError(
                {"cohort": "시험(exam)과 기수(cohort)의 과정(course)이 일치하지 않습니다."}
            )

        return attrs


# ---------------
# API용 시리얼라이저
# ---------------


class ErrorResponseSerializer(serializers.Serializer[dict[str, Any]]):
    error_detail: serializers.CharField = serializers.CharField()


class DeploymentListItemSerializer(serializers.Serializer[dict[str, Any]]):
    deployment_id: serializers.IntegerField = serializers.IntegerField()
    exam_title: serializers.CharField = serializers.CharField()
    subject_name: serializers.CharField = serializers.CharField()
    cohort_number: serializers.IntegerField = serializers.IntegerField()
    course_name: serializers.CharField = serializers.CharField()
    submit_count: serializers.IntegerField = serializers.IntegerField()
    avg_score: serializers.FloatField = serializers.FloatField(allow_null=True)
    status: serializers.ChoiceField = serializers.ChoiceField(choices=DeploymentStatus.choices)
    created_at: serializers.DateTimeField = serializers.DateTimeField()


class DeploymentListResponseSerializer(serializers.Serializer[dict[str, Any]]):
    page: serializers.IntegerField = serializers.IntegerField()
    size: serializers.IntegerField = serializers.IntegerField()
    total_count: serializers.IntegerField = serializers.IntegerField()
    deployments: serializers.ListSerializer[Any] = serializers.ListSerializer(child=DeploymentListItemSerializer())

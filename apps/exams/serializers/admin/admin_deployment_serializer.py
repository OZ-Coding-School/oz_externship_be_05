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
        read_only_fields = ("id", "access_code", "status")

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

        # update 시작된 시험 시간 변경 불가
        if isinstance(instance, ExamDeployment) and "open_at" in attrs:
            DeploymentValidator.validate_not_started(
                open_at=instance.open_at,
                status=instance.status,
            )

        # 시험 시간 최소값
        duration_time = attrs.get("duration_time")
        if duration_time is not None and duration_time <= 29:
            raise serializers.ValidationError({"duration_time": "시험 시간은 30분 이상이어야 합니다."})

        # exam - cohort 관계 검증
        exam = attrs.get("exam", getattr(instance, "exam", None))
        cohort = attrs.get("cohort", getattr(instance, "cohort", None))
        if exam and cohort and exam.subject.course_id != cohort.course_id:
            raise serializers.ValidationError(
                {"cohort": "시험(exam)과 기수(cohort)의 과정(course)이 일치하지 않습니다."}
            )

        return attrs


# ----- 조회용 -----
class AdminDeploymentListItemSerializer(serializers.ModelSerializer[ExamDeployment]):
    deployment_id = serializers.IntegerField(source="id")
    exam_title = serializers.CharField(source="exam.title")
    subject_name = serializers.CharField(source="exam.subject.title")
    course_name = serializers.CharField(source="cohort.course.name")
    cohort_number = serializers.IntegerField(source="cohort.number")

    submit_count = serializers.IntegerField()
    avg_score = serializers.FloatField(allow_null=True)

    class Meta:
        model = ExamDeployment
        fields = [
            "deployment_id",
            "exam_title",
            "subject_name",
            "course_name",
            "cohort_number",
            "submit_count",
            "avg_score",
            "status",
            "created_at",
        ]


class AdminDeploymentListResponseSerializer(serializers.Serializer[Any]):
    page = serializers.IntegerField()
    size = serializers.IntegerField()
    total_count = serializers.IntegerField()
    deployments = AdminDeploymentListItemSerializer(many=True)


class AdminDeploymentCreateResponseSerializer(serializers.Serializer[Any]):
    exam_id = serializers.IntegerField()
    cohort_id = serializers.IntegerField()
    duration_time = serializers.IntegerField()
    access_code = serializers.CharField()
    open_at = serializers.DateTimeField()
    close_at = serializers.DateTimeField()

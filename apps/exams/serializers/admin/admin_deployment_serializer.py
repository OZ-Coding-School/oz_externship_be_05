from typing import Any, Dict

from rest_framework import serializers

from apps.courses.models.cohorts_models import Cohort
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


# 배포 생성 응답
class AdminDeploymentCreateResponseSerializer(serializers.Serializer[Any]):
    pk = serializers.IntegerField()


# ----- 리스트 조회용 -----
class ExamSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    title = serializers.CharField()
    thumbnail_img_url = serializers.CharField()


class SubjectSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    name = serializers.CharField(source="title")


class CourseSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    name = serializers.CharField()
    tag = serializers.CharField()


class CohortSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    number = serializers.IntegerField()
    display = serializers.SerializerMethodField()
    course = CourseSerializer()

    def get_display(self, obj: Cohort) -> str:
        return f"{obj.course.name} {obj.number}기"


class AdminDeploymentListItemSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    submit_count = serializers.IntegerField()
    avg_score = serializers.FloatField(allow_null=True)
    status = serializers.CharField()
    exam = ExamSerializer()
    subject = SubjectSerializer(source="exam.subject")
    cohort = CohortSerializer()
    created_at = serializers.DateTimeField()


# 리스트 응답
class AdminDeploymentListResponseSerializer(serializers.Serializer[Any]):
    count = serializers.IntegerField()
    previous = serializers.CharField(allow_null=True)
    next = serializers.CharField(allow_null=True)
    results = AdminDeploymentListItemSerializer(many=True)

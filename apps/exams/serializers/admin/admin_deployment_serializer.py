from typing import Any, Dict, cast

from rest_framework import serializers

from apps.courses.models.cohorts_models import Cohort
from apps.exams.models import Exam, ExamDeployment
from apps.exams.models.exam_deployment import DeploymentStatus
from apps.exams.services.admin.validators.deployment_validator import (
    DeploymentValidator,
)
from config.settings.base import FRONTEND_DOMAIN


# 시험 배포 데이터 검증
class AdminDeploymentPostSerializer(serializers.ModelSerializer[ExamDeployment]):
    """
    시험 배포 데이터 생성 검증용 시리얼라이저
    - 시간 검증
    - 시험-기수 관계 검증
    - 시험 시간(duration_time) 검증
    """

    exam_id = serializers.IntegerField(write_only=True, required=True)
    cohort_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = ExamDeployment
        fields = [
            "exam_id",
            "cohort_id",
            "duration_time",
            "open_at",
            "close_at",
        ]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        open_at = attrs.get("open_at")
        close_at = attrs.get("close_at")

        # open_at < close_at
        if open_at and close_at:
            DeploymentValidator.validate_time(open_at, close_at)

        # create 일 경우
        if open_at:
            DeploymentValidator.validate_open(open_at)

        duration_time = attrs.get("duration_time")
        if duration_time is not None and duration_time < 30:
            raise serializers.ValidationError({"duration_time": "시험 시간은 30분 이상이어야 합니다."})

        exam = Exam.objects.filter(id=attrs["exam_id"]).first()
        cohort = Cohort.objects.filter(id=attrs["cohort_id"]).first()

        if not exam or not cohort:
            raise serializers.ValidationError("exam 또는 cohort를 찾을 수 없습니다.")

        if exam.subject.course_id != cohort.course_id:
            raise serializers.ValidationError(
                {"cohort_id": "시험(exam)과 기수(cohort)의 과정(course)이 일치하지 않습니다."}
            )

        attrs["exam"] = exam
        attrs["cohort"] = cohort
        return attrs


class AdminDeploymentPatchSerializer(serializers.ModelSerializer[ExamDeployment]):
    """
    시험 배포 데이터 수정 검증용 시리얼라이저
    """

    class Meta:
        model = ExamDeployment
        fields = [
            "open_at",
            "close_at",
            "duration_time",
        ]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        instance = cast(ExamDeployment, self.instance)

        open_at = attrs.get("open_at", instance.open_at)
        close_at = attrs.get("close_at", instance.close_at)

        DeploymentValidator.validate_time(open_at, close_at)

        if "open_at" in attrs:
            DeploymentValidator.validate_not_started(
                open_at=instance.open_at,
                status=instance.status,
            )

        # 시험 시간 최소값
        duration_time = attrs.get("duration_time")
        if duration_time is not None and duration_time < 30:
            raise serializers.ValidationError({"duration_time": "시험 시간은 30분 이상이어야 합니다."})

        return attrs


# 배포 상태 수정 검증
class AdminDeploymentStatusPatchSerializer(serializers.Serializer[Any]):
    """
    시험 배포 상태 수정 검증용 시리얼라이저
    """

    status = serializers.CharField()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        status_value = attrs.get("status")
        if status_value not in [DeploymentStatus.ACTIVATED, DeploymentStatus.DEACTIVATED]:
            raise serializers.ValidationError("유효하지 않은 배포 상태입니다.")
        return attrs


# ----------------------
# 공통 참조용 시리얼라이저
# ----------------------
class ExamResponseSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    title = serializers.CharField()
    thumbnail_img_url = serializers.CharField()


class SubjectResponseSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    name = serializers.CharField(source="title")


class CourseResponseSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    name = serializers.CharField()
    tag = serializers.CharField()


class CohortResponseSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    number = serializers.IntegerField()
    display = serializers.SerializerMethodField()
    course = CourseResponseSerializer()

    def get_display(self, obj: Cohort) -> str:
        return f"{obj.course.name} {obj.number}기"


class DeploymentResponseSerializer(serializers.ModelSerializer[ExamDeployment]):
    exam_access_url = serializers.SerializerMethodField()
    submit_count = serializers.SerializerMethodField()
    not_submitted_count = serializers.SerializerMethodField()
    cohort = CohortResponseSerializer()

    class Meta:
        model = ExamDeployment
        fields = [
            "id",
            "exam_access_url",
            "access_code",
            "cohort",
            "submit_count",
            "not_submitted_count",
            "duration_time",
            "open_at",
            "close_at",
            "created_at",
        ]

    def get_exam_access_url(self, obj: ExamDeployment) -> str:
        return f"{FRONTEND_DOMAIN}/exams/deployments/{obj.id}/"

    def get_submit_count(self, obj: ExamDeployment) -> int:
        return getattr(obj, "submit_count", 0)

    def get_not_submitted_count(self, obj: ExamDeployment) -> int:
        return getattr(obj, "not_submitted_count", 0)


class DeploymentListItemSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    submit_count = serializers.IntegerField()
    avg_score = serializers.FloatField(allow_null=True)
    status = serializers.CharField()
    exam = ExamResponseSerializer()
    subject = SubjectResponseSerializer(source="exam.subject")
    cohort = CohortResponseSerializer()
    created_at = serializers.DateTimeField()


# ----------------------
# 응답 시리얼라이저
# ----------------------


# 배포 생성 응답
class AdminDeploymentCreateResponseSerializer(serializers.Serializer[Any]):
    pk = serializers.IntegerField()


# 배포 리스트 응답
class AdminDeploymentListResponseSerializer(serializers.Serializer[Any]):
    count = serializers.IntegerField()
    previous = serializers.CharField(allow_null=True)
    next = serializers.CharField(allow_null=True)
    results = DeploymentListItemSerializer(many=True)


# 배포 디테일 응답
class AdminDeploymentDetailResponseSerializer(DeploymentResponseSerializer):
    exam = ExamResponseSerializer()
    subject = SubjectResponseSerializer(source="exam.subject")

    class Meta:
        model = ExamDeployment
        fields = DeploymentResponseSerializer.Meta.fields + ["exam", "subject"]


# 배포 수정 응답
class AdminDeploymentUpdateResponseSerializer(serializers.Serializer[Any]):
    deployment_id = serializers.IntegerField(source="id")
    duration_time = serializers.IntegerField()
    open_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    close_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

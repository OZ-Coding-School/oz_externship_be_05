from __future__ import annotations

from typing import Any, Dict

from django.utils import timezone
from rest_framework import serializers

from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.models.exam_submission import ExamSubmission
from apps.exams.services.student.exam_submit_service import (
    create_exam_submission,
    validate_exam_submission_limit,
)


class ExamSubmissionCreateSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """
    수강생 쪽지시험 제출 요청용 serializer
    """

    # 시작시간
    started_at = serializers.DateTimeField(required=True, allow_null=True, help_text="시험시작시간")

    # 부정행위
    cheating_count = serializers.IntegerField(
        min_value=0,
        default=0,
        help_text="부정행위 횟수",
    )

    # 정답
    answers = serializers.JSONField(
        help_text="정답 (JSON)",
    )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        deployment: ExamDeployment = self.context["deployment"]
        submitter: Any = self.context["request"].user

        # 제출 횟수 제한 검증(Service)
        validate_exam_submission_limit(deployment=deployment, submitter=submitter)

        started_at = attrs["started_at"]

        now = timezone.now()
        elapsed = (now - started_at).total_seconds()

        # started_at 미래인 경우 오류
        if elapsed < 0:
            raise serializers.ValidationError({"started_at": "시작시간은 현재 시간보다 빨라야합니다."})

        # 시간 제한 검증
        duration_time = getattr(deployment, "duration_time", None)

        # 시간초과 여부 > 즉시실패
        is_time_over = False
        if duration_time is not None and elapsed > duration_time:
            raise serializers.ValidationError("시험 제한 시간이 초과되어 제출할 수 없습니다")
        attrs["elapsed_seconds"] = int(elapsed)
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> ExamSubmission:
        deployment: ExamDeployment = self.context["deployment"]
        submitter = validated_data["submitter"]

        return create_exam_submission(
            deployment=deployment,
            submitter=submitter,
            started_at=validated_data["started_at"],
            cheating_count=validated_data["cheating_count"],
            raw_answers=validated_data["answers"],
        )

    def to_representation(self, instance: ExamSubmission) -> Dict[str, Any]:
        # 응답은 채점 결과 확인 페이지로 이동할 때 필요한 최소 정보만 내려주기
        return {
            "id": instance.pk,
            "deployment_id": instance.deployment_id,
        }

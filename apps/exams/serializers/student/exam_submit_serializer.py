from __future__ import annotations

from typing import Any, Dict

from django.utils import timezone
from rest_framework import serializers

from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.models.exam_submission import ExamSubmission
from apps.exams.services.student.exam_submit_service import create_exam_submission


class ExamSubmissionCreateSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """
    수강생 쪽지시험 제출 요청용 serializer
    """

    # 시작시간
    started_at = serializers.DateTimeField(
        required=False,
        help_text="시험시작시간",
    )

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
        request = self.context["request"]
        deployment: ExamDeployment = self.context["deployment"]

        # 이미 제출한 시험인지
        if ExamSubmission.objects.filter(
            deployment=deployment,
            submitter=request.user,
        ).exists():
            raise serializers.ValidationError("이미 해당 쪽지시험을 제출했습니다.")

        # started_at 필수 + None 허용 안 함
        started_at = attrs.get("started_at")
        if started_at is None:
            raise serializers.ValidationError({"started_at": "started_at 필드는 필수입니다."})

        # 시간 제한 검증
        duration_time = getattr(deployment, "duration_time", None)

        now = timezone.now()
        elapsed = (now - started_at).total_seconds()

        # started_at 미래인 경우 오류
        if elapsed < 0:
            raise serializers.ValidationError({"started_at": "시작시간이 올바르지 않습니다."})

        # 시간초과 여부 (막지는 않고 상태만 넘김)
        is_time_over = False
        if duration_time is not None:
            is_time_over = elapsed > duration_time

        attrs["elapsed_seconds"] = int(elapsed)
        attrs["is_time_over"] = is_time_over
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> ExamSubmission:
        request = self.context["request"]
        deployment: ExamDeployment = self.context["deployment"]

        submission = create_exam_submission(
            deployment=deployment,
            submitter=request.user,
            started_at=validated_data["started_at"],
            cheating_count=validated_data["cheating_count"],
            raw_answers=validated_data["answers"],
            # elapsed_seconds=validated_data["elapsed_seconds"],
            # is_time_over=validated_data["is_time_over"],
        )
        return submission

    def to_representation(self, instance: ExamSubmission) -> Dict[str, Any]:
        """
        응답은 채점 결과 확인 페이지로 이동할 때 필요한 최소 정보만 내려주기
        """
        return {
            "id": instance.pk,
            "deployment_id": instance.deployment_id,
            "score": instance.score,
            "correct_answer_count": instance.correct_answer_count,
            "cheating_count": instance.cheating_count,
            "started_at": instance.started_at,
            "submitted_at": instance.created_at,
        }

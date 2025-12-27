from typing import Any, Dict

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models import ExamDeployment
from apps.exams.models.exam_question import QuestionType
from apps.exams.models.exam_submission import ExamSubmission
from apps.exams.services.student.exam_submit_service import (
    create_exam_submission,
    validate_exam_submission_limit,
)
from apps.user.models import User
from config.settings.base import FRONTEND_DOMAIN


class AnswerItemSerializer(serializers.Serializer[Any]):
    question_id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=QuestionType.choices)
    submitted_answer = serializers.JSONField()


class ExamSubmissionCreateSerializer(serializers.Serializer[Any]):
    """
    수강생 쪽지시험 제출 요청용 serializer
    """

    submitter_id = serializers.IntegerField(required=True)

    # 시작시간
    started_at = serializers.DateTimeField(required=True, allow_null=True, help_text="시험시작시간")

    # 부정행위
    cheating_count = serializers.IntegerField(min_value=0, default=0, help_text="부정행위 횟수")

    # 정답
    answers = AnswerItemSerializer(many=True, help_text="문항별 제출 답안")

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:

        deployment: ExamDeployment = self.context["deployment"]
        submitter = get_object_or_404(User, pk=attrs["submitter_id"])

        attrs["submitter"] = submitter
        attrs["deployment"] = deployment

        # 409: 제출 횟수 제한
        validate_exam_submission_limit(deployment=deployment, submitter=submitter)

        now = timezone.now()
        started_at = attrs["started_at"]

        # 400: started_at 미래인 경우 오류 → 세션 무결성 문제
        if started_at > now:
            raise serializers.ValidationError(EMS.E400_INVALID_SESSION("시험 응시"))

        # 시간 초과 시 자동 제출
        attrs["is_auto_submitted"] = deployment.close_at is not None and now > deployment.close_at

        return attrs

    def create(self, validated_data: Dict[str, Any]) -> ExamSubmission:
        return create_exam_submission(
            deployment=validated_data["deployment"],
            submitter=validated_data["submitter"],
            started_at=validated_data["started_at"],
            cheating_count=validated_data["cheating_count"],
            raw_answers=validated_data["answers"],
            is_auto_submitted=validated_data.get("is_auto_submitted", False),
        )

    def to_representation(self, instance: ExamSubmission) -> Dict[str, Any]:
        return {
            "submission_id": instance.pk,
            "score": instance.score,
            "correct_answer_count": instance.correct_answer_count,
            "redirect_url": f"{FRONTEND_DOMAIN}/exam/submissions/{instance.pk}/",
        }

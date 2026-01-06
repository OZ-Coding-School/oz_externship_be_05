from __future__ import annotations

from datetime import datetime
from typing import Any

from django.utils import timezone
from rest_framework import serializers

from apps.exams.models.exam_submission import ExamSubmission


class AnswerSerializer(serializers.Serializer[Any]):
    question_id = serializers.IntegerField(write_only=True)
    submitted_answer = serializers.ListField(child=serializers.CharField(), write_only=True)


class ExamSubmissionCreateSerializer(serializers.ModelSerializer[ExamSubmission]):
    """
    수강생 쪽지시험 제출 요청용 serializer
    """

    # 정답
    answers = AnswerSerializer(many=True, write_only=True)

    class Meta:
        model = ExamSubmission
        fields = [
            "id",
            "deployment",
            "started_at",
            "cheating_count",
            "answers",
        ]

    def validate_started_at(self, value: datetime) -> datetime:
        now = timezone.now()
        # started_at 미래인 경우 오류
        if value > now:
            raise serializers.ValidationError("시작시간은 현재 시간보다 빨라야합니다.")

        return value

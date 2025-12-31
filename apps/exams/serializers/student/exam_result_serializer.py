from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.exams.models import Exam, ExamSubmission
from apps.exams.models.exam_question import QuestionType


class ExamSerializer(serializers.ModelSerializer[Exam]):
    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "thumbnail_img_url",
        ]


class ExamResultQuestionSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField(read_only=True)
    question = serializers.CharField(read_only=True)
    prompt = serializers.CharField(read_only=True)
    blank_count = serializers.IntegerField(read_only=True)
    options = serializers.ListField(child=serializers.CharField(), read_only=True)
    type = serializers.ChoiceField(choices=QuestionType.choices, read_only=True)
    answer = serializers.ListField(child=serializers.CharField(), read_only=True, help_text="문제 정답")
    point = serializers.IntegerField(read_only=True)
    explanation = serializers.CharField(read_only=True)
    is_correct = serializers.BooleanField(read_only=True, help_text="문제를 맞혔는지 여부")
    submitted_answer = serializers.ListField(
        child=serializers.CharField(), read_only=True, help_text="사용자가 제출한 정답"
    )


class ExamResultSerializer(serializers.ModelSerializer[ExamSubmission]):
    """
    시험 결과 조회 API의 최상위 응답 Serializer
    """

    exam = ExamSerializer(source="deployment.exam", read_only=True)
    elapsed_time = serializers.TimeField(read_only=True)
    questions = ExamResultQuestionSerializer(source="result_questions", many=True, read_only=True)
    total_score = serializers.IntegerField(source="score", read_only=True)
    submitted_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = ExamSubmission
        fields = [
            "id",
            "submitter_id",
            "deployment_id",
            "exam",
            "questions",
            "cheating_count",
            "total_score",
            "correct_answer_count",
            "elapsed_time",
            "started_at",
            "submitted_at",
        ]

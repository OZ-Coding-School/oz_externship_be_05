from rest_framework import serializers

from apps.exams.models import ExamQuestion


class ExamQuestionDetailSerializer(serializers.ModelSerializer[ExamQuestion]):
    """
    GET /api/v1/admin/exams/{exam_id} 요청 시 사용되는 목록 조회 시리얼라이저입니다.
    """

    question_id = serializers.IntegerField(source="id")  # question_id로 필드이름변경
    options = serializers.JSONField()  # JSONField(options)는 이미 파이썬 리스트
    correct_answer = serializers.JSONField(source="answer")

    class Meta:
        model = ExamQuestion
        fields = ["question_id", "type", "question", "prompt", "point", "options", "correct_answer"]

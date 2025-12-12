from typing import Any  # mypy를 위해 추가

from rest_framework import serializers

# 실제 경로로 수정 필요
from apps.exams.models.exam_deployment import ExamDeployment


class StudentExamAccessSerializer(serializers.ModelSerializer[Any]):  # [Any] 추가
    exam_id = serializers.IntegerField(source="exam.id", read_only=True)
    exam_title = serializers.CharField(source="exam.title", read_only=True)
    time_limit = serializers.IntegerField(source="duration_time", read_only=True)

    class Meta:
        model = ExamDeployment
        fields = [
            "id",
            "access_code",
            "open_at",
            "close_at",
            "time_limit",
            "exam_id",
            "exam_title",
            "questions_snapshot",
        ]

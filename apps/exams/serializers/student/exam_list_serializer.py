from typing import Any  # mypy를 위해 추가

from rest_framework import serializers

from apps.exams.models.exam import Exam  # 실제 경로로 수정 필요


class ExamListSerializer(serializers.ModelSerializer[Any]):  # [Any] 추가
    subject_title = serializers.CharField(source="subject.title", read_only=True)

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "thumbnail_img_url",
            "subject_title",
            "created_at",
        ]

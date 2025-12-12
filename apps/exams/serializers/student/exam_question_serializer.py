from typing import Any  # mypy를 위해 추가

from rest_framework import serializers


class ExamQuestionSerializer(serializers.Serializer[Any]):  # [Any] 추가
    question_id = serializers.IntegerField(help_text="문항 ID")
    question_type = serializers.CharField(max_length=50, help_text="문항 유형")
    content = serializers.CharField(help_text="문항 내용")
    options = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True, help_text="선택지 목록"
    )

from typing import Any

from rest_framework import serializers


class AnswerSpecSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField(read_only=True)
    question = serializers.IntegerField(help_text="질문 ID")
    content = serializers.CharField(help_text="답변 내용")
    created_at = serializers.DateTimeField(read_only=True)

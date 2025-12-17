from typing import Any

from rest_framework import serializers


# 요청용 질문 id는 url에있으니 body에서 제거
class AnswerSpecRequestSerializer(serializers.Serializer[Any]):
    content = serializers.CharField(help_text="답변 내용")


# 응답용
class AnswerSpecResponseSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField(read_only=True)
    question = serializers.IntegerField(help_text="질문 ID")
    content = serializers.CharField(help_text="답변 내용")
    created_at = serializers.DateTimeField(read_only=True)

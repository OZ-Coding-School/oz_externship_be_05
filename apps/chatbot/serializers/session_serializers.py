from typing import Any

from rest_framework import serializers

from apps.chatbot.models.chatbot_sessions import ChatbotSession, ChatModel
from apps.qna.models import Question


# Session의 응답포멧
class SessionSerializer(serializers.ModelSerializer[ChatbotSession]):
    class Meta:
        model = ChatbotSession
        fields = ["id", "user", "question", "title", "using_model", "created_at", "updated_at"]
        read_only_fields = fields


# 한 시리얼라이저로 요청이랑 응답 스키마를 만들 수 있다. write_only랑 read_only 속성을 잘 사용
class SessionCreateSerializer(serializers.ModelSerializer[ChatbotSession]):
    class Meta:
        model = ChatbotSession
        fields = ["id", "user", "question", "title", "using_model", "created_at", "updated_at"]
        extra_kwargs = {
            "id": {"read_only": True},
            "question": {"required": True},
            "user": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "title": {"required": False},  # 없을 경우 New Chat 적용
            "using_model": {"required": True},
        }

    def validate_question(self, value: Question) -> Question:
        request = self.context["request"]
        user = request.user

        if value.author != user:
            raise serializers.ValidationError("본인이 작성한 질문에 대해서만 세션을 만들 수 있습니다.")
        return value

    def create(self, validated_data: dict[str, Any]) -> ChatbotSession:
        request = self.context["request"]
        user = request.user

        question = validated_data["question"]
        title = validated_data.get("title") or "New Chat"
        using_model = validated_data["using_model"]

        session: ChatbotSession = ChatbotSession.objects.create(
            user=user,
            question=question,
            title=title,
            using_model=using_model,
        )
        return session

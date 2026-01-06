from rest_framework import serializers

from apps.chatbot.models.chatbot_completions import ChatbotCompletion


# Completion의 응답 포멧
class CompletionSerializer(serializers.ModelSerializer[ChatbotCompletion]):
    class Meta:
        model = ChatbotCompletion
        fields = ["id", "session", "message", "role", "created_at", "updated_at"]
        read_only_fields = fields


# completion 생성: POST
class CompletionCreateSerializer(serializers.ModelSerializer[ChatbotCompletion]):
    message = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = ChatbotCompletion
        fields = ["id", "session", "message", "role", "created_at", "updated_at"]
        extra_kwargs = {
            "id": {"read_only": True},
            "session": {"read_only": True},
            "role": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
        }

from rest_framework import serializers

from apps.aichatbot.models.chatbot_completions import ChatbotCompletion
from apps.aichatbot.models.chatbot_sessions import ChatbotSession
from apps.question.models import Question


# 세션 생성 요청(question_id 받기)
class SessionCreateSerializer(serializers.ModelSerializer[Question]):
    # question_id = serializers.IntegerField(
    #     write_only=True,
    #     help_text="Question ID",
    # )

    class Meta:
        model = ChatbotSession
        fields = "__all__"
        read_only_fields = fields


# 세션 목록 조회 응답
class SessionListSerializer(serializers.ModelSerializer[Question]):
    # question_id = serializers.IntegerField(source="question_id", read_only=True)
    # question_title = serializers.CharField(
    #     source="question.title",
    #     read_only=True,
    #     help_text="Question's title",
    # )

    class Meta:
        model = ChatbotSession
        fields = "__all__"
        read_only_fields = fields


# 채팅 요청(prompt 받기)
class CompletionCreateSerializer(serializers.ModelSerializer[ChatbotCompletion]):

    class Meta:
        model = ChatbotCompletion
        fields = "__all__"
        read_only_fields = fields


# 대화 내역 응답하기
class CompletionListSerializer(serializers.ModelSerializer[ChatbotCompletion]):

    class Meta:
        model = ChatbotCompletion
        fields = "__all__"
        read_only_fields = fields

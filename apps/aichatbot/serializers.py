from datetime import datetime

from rest_framework import serializers

from apps.aichatbot.models.chatbot_completions import ChatbotCompletion, UserRole
from apps.aichatbot.models.chatbot_sessions import ChatbotSession, ChatModel

"""
이 파일의 목적 (SPEC API 단계)
- "JSON 받아오기": request.data를 어떤 필드/타입으로 받을지 정의 + 기본 검증(필수/길이/형식)
- "JSON 포매팅": 응답을 어떤 키 구조로 반환할지(일관된 response schema) 정의

세션
- POST 세션 생성 (Request/Response 스키마)
- GET 세션 목록 (Response 스키마)

세션 상세
- GET 세션의 대화내역 목록 (Response 스키마)
- DELETE 세션의 대화내역 전체 삭제 (Response 스키마)

메세지 생성
- POST 사용자 입력 받아 답변 생성
  - 수정사항: "prompt" 칼럼 삭제 → 요청 필드명은 content/message 같은 것으로 통일 권장

스트리밍
- 별도 엔드포인트로 분리
- SPEC 단계에선 501로 스킵 예정 → serializer는 보통 필요 없음(에러 응답 포맷만 통일)
"""


# apps/aichatbot/serializers.py
# Session의 응답포멧
class SessionSerializer(serializers.ModelSerializer[ChatbotSession]):
    class Meta:
        model = ChatbotSession
        fields = ["id", "question", "title", "using_model", "created_at", "updated_at"]
        read_only_fields = fields


# 세션 생성 요청(question_id 받기)
class SessionCreateSerializer(serializers.ModelSerializer[ChatbotSession]):
    question = serializers.IntegerField(help_text="Question ID(FK)")
    # spec API에서만 이렇게
    title = serializers.CharField(required=False, allow_blank=True, max_length=30)
    using_model = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    class Meta:
        model = ChatbotSession
        fields = ["id", "user", "question", "title", "using_model", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "question", "created_at"]


# Completion의 응답 포멧
class CompletionSerializer(serializers.ModelSerializer[ChatbotCompletion]):
    class Meta:
        model = ChatbotCompletion
        fields = ["id", "session", "message", "role", "created_at", "updated_at"]
        read_only_fields = fields


# completion 생성 (요청 - Request)
class CompletionCreateSerializer(serializers.ModelSerializer[ChatbotCompletion]):
    message = serializers.CharField(required=False, allow_blank=True)
    # class Meta:
    #     model = ChatbotCompletion
    #     fields = "__all__"
    #     read_only_fields = fields

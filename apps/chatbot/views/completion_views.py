from typing import Union

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chatbot.models import ChatbotCompletion, ChatbotSession
from apps.chatbot.serializers.completion_serializers import (
    CompletionCreateSerializer,
    CompletionSerializer,
)


class CompletionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # session 존재여부 검증
    def _get_session_check(self, session_id: int) -> ChatbotSession:
        try:
            return ChatbotSession.objects.get(id=session_id)
        except ChatbotSession.DoesNotExist:
            raise NotFound("Session not found")

    # 세션 종속여부 확인
    def _session_dependency(self, session: ChatbotSession, user: Union[AbstractBaseUser, AnonymousUser]) -> None:
        if session.user != user:
            raise NotFound("Session not found")

    def _ai_chat_response(self, session: ChatbotSession, user_message: str) -> ChatbotCompletion:
        # ai 챗봇 답변. services에서 구현
        ai_response = f"Reply to '{user_message}'"

        # AI 응답 DB에 저장
        ai_completion = ChatbotCompletion.objects.create(
            session=session,
            message=ai_response,
            role="assistant",
        )

        return ai_completion

    @extend_schema(
        tags=["AI 챗봇"],
        summary="AI 챗봇 응답 생성 API",
        description="AI 챗봇과 사용자의 메세지를 생성/저장하는 API. user 메세지 저장 → AI 응답 생성·저장, 이후 둘 다 반환",
        request=CompletionCreateSerializer,
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.INT,
                location="path",
                description="세션 고유 ID 값",
            ),
        ],
        responses={
            "201": {
                "type": "string",
                "example": {
                    "user_completion": {
                        "id": 1,
                        "session": 1,
                        "message": "python이 뭐야?",
                        "role": "user",
                        "created_at": "2025-01-01",
                    },
                    "ai_completion": {
                        "id": 2,
                        "session": 1,
                        "message": "python 설명",
                        "role": "assistant",
                        "created_at": "2025-01-01",
                    },
                },
                "description": "SSE 스트리밍 응답",
            },
            "400": {"type": "object", "example": {"error_detail": "Message field is essential"}},
            "401": {"type": "object", "example": {"error_detail": "Authentication credentials were not provided."}},
            "404": {"type": "object", "example": {"error_detail": "Session not found"}},  # 403 대신 사용
        },
    )

    # completion 대화 생성
    def post(self, request: Request, session_id: int) -> Response:
        # 세션 검증
        session = self._get_session_check(session_id)
        self._session_dependency(session, request.user)

        # 요청 데이터 검증, 사용자 메세지 저장
        serializer = CompletionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_completion: ChatbotCompletion = serializer.save(session=session, role="user")

        # ai 응답 생성, 저장
        ai_completion = self._ai_chat_response(session, user_completion.message)

        return Response(
            {
                "user_completion": CompletionSerializer(user_completion).data,
                "ai_completion": CompletionSerializer(ai_completion).data,
            },
            status=status.HTTP_201_CREATED,
        )

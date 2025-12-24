from __future__ import annotations

from asgiref.sync import sync_to_async
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chatbot.models.chatbot_sessions import ChatbotSession
from apps.chatbot.serializers.completion_serializers import (
    CompletionCreateSerializer,
)
from apps.chatbot.services.completion_response_service import (
    create_streaming_response,
    user_message_save,
)

# SSE 스트리밍 AI 응답 생성 API
class CompletionStreamAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["AI 챗봇"],
        summary="AI 챗봇 응답 생성 API with Streaming",
        description="AI 챗봇과 사용자의 메세지를 생성/저장하는 API. user 메세지 저장 → AI 응답 생성·저장, 이후 둘 다 반환",
        request=CompletionCreateSerializer,
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=OpenApiTypes.INT,
                location="path",
                description="세션 PK ID",
            ),
        ],
        responses={
            "200": {
                "type": "string",
                "description": "SSE 스트리밍 응답",
            },
            "400": {"type": "object", "example": {"error_detail": "Message field is essential"}},
            "401": {"type": "object", "example": {"error_detail": "Authentication credentials were not provided."}},
            "403": {"type": "object", "example": {"error_detail": "Session does not exist."}},
            "404": {"type": "object", "example": {"error_detail": "Session not found"}},
        },
    )

    # SSE 스트리밍 응답 생성.
    def post(self, request: Request, session_id: int) -> StreamingHttpResponse:
        session = get_object_or_404(ChatbotSession, id=session_id, user=request.user)

        # 요청 데이터 검증
        serializer = CompletionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_message = serializer.validated_data["message"]

        # 사용자 메세지 저장 (service에서 호출해서)
        user_message_save(
            session=session,
            message=user_message,
        )

        return create_streaming_response(
            session=session,
            user_message=user_message,
        )

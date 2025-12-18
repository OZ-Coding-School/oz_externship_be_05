from typing import Optional

from django.contrib.auth import user_logged_in
from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied


from apps.chatbot.models import ChatbotSession, ChatbotCompletion
from apps.chatbot.serializers.completion_serializers import CompletionSerializer, CompletionCreateSerializer


class CompletionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # session 존재여부 검증
    def _get_session_check(self, session_id: int) -> ChatbotSession:
        if ChatbotSession.objects.filter(id=session_id).exists():
            return ChatbotSession.objects.get(id=session_id)
        else:
            raise NotFound("Session not found")

    # 세션 종속여부 확인(are you my master?)
    # 본인 아닐 시
    def _validate_session_master(self, session: ChatbotSession, user: AbstractBaseUser) -> Optional[PermissionDenied]:
        if not session.user == user:
            raise PermissionDenied("You are not authorized")

    # SSE 응답 by chatbot
    def _stream_assistant_response(self, session: ChatbotSession, user_message: str) -> Response:
        # 로직 적기...뭐적어야하냐...

    @extend_schema(
        tags = ["Completion"],
        summary = "챗봇 응답 생성 API: SSE 스트리밍",
        request = CompletionCreateSerializer,
        parameters = [
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="세션 고유 ID 값",
            ),
        ],
        responses = {
            "200" : {"type": "string", "description": "SSE 스트리밍 응답",},
            "400" : {"type": "object", "example": {"error_detail": "Message field is essential"}},
            "401" : {"type": "object", "example": {"error_detail": "Authentication credentials were not provided."}},
            "403" : {"type": "object", "example": {"error_detail": "No permission for this action"}},
            "404" : {"type": "object", "example": {"error_detail": "Session not found"}},
        },
    )

    #
    def post(self, request: Request, pk: int) -> Response:
        # 세션 검증
        session = self._get_session_check(pk)
        self._validate_session_master(session, request.user)

        # 요청 데이터 검증, 사용자 메세지 저장
        serializer = CompletionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        completion = serializer.save(session=session)

        return Response(serializer.data)

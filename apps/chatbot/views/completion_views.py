from __future__ import annotations

from typing import cast

from django.db.models import QuerySet
from django.http import StreamingHttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chatbot.models import ChatbotCompletion
from apps.chatbot.models.chatbot_sessions import ChatbotSession
from apps.chatbot.serializers.completion_serializers import (
    CompletionCreateSerializer,
    CompletionSerializer,
)
from apps.chatbot.services.completion_response_service import (
    create_streaming_response,
    user_message_save,
)
from apps.core.exceptions.exception_messages import EMS
from apps.user.models import User


class CustomCursorPagination(CursorPagination):
    cursor_query_param = "cursor"
    page_size_query_param = "page_size"
    page_size = 10
    max_page_size = 50
    ordering = "-created_at"


# SSE 스트리밍 AI 응답 생성 API
class CompletionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination
    serializer_class = CompletionSerializer

    # 세션 조회, 권한 검증 (여기서)
    def get_session(self, session_id: int) -> ChatbotSession:
        user = cast(User, self.request.user)
        session = ChatbotSession.objects.filter(user=user, id=session_id).first()
        if session is None:
            raise NotFound(EMS.E404_CHATBOT_SESSION_NOT_FOUND)
        return session

    # 세션 속한 모든 메세지 조회, 기본 쿼리셋 반환
    def get_queryset(self, session: ChatbotSession) -> QuerySet[ChatbotCompletion]:
        return session.messages.all()

    # POST (메세지 작성, AI 응답 생성)
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
                "example": 'data: {"contents": "안녕하세요"}\n\ndata: [DONE]\n\n',
            },
            "204": {"type": "object", "example": ""},  # 204 내역
            "400": {"type": "object", "example": EMS.E400_REQUIRED_FIELD},
            "401": {"type": "object", "example": EMS.E401_USER_ONLY_ACTION("채팅")},
            "403": {"type": "object", "example": EMS.E403_PERMISSION_DENIED("채팅")},
        },
    )

    # SSE 스트리밍 응답 생성.
    def post(self, request: Request, session_id: int) -> StreamingHttpResponse:
        session = self.get_session(session_id)  # 세션 조회(권한 검증 포함)

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

    # 메세지 목록 조회
    @extend_schema(
        tags=["AI 챗봇"],
        summary="챗봇 대화 내역 조회",
        parameters=[
            OpenApiParameter(
                name="cursor", type=OpenApiTypes.STR, description="커서 페이지 네이션 적용을 위한 커서 값", required=False, default=None,
            ),
            OpenApiParameter(
                name="page_size", type=OpenApiTypes.INT, description="페이지 네이션 사이즈 지정을 위한 값", default=10
            ),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "next": {"type": "string", "nullable": True},
                    "previous": {"type": "string", "nullable": True},
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "message": {"type": "string"},
                                "role": {"type": "string"},
                                "created_at": {"type": "string", "format": "date-time"},
                            },
                        },
                    },
                },
            },
            401: {"type": "object", "example": EMS.E401_USER_ONLY_ACTION("조회")},
            404: {"type": "object", "example": EMS.E404_CHATBOT_SESSION_NOT_FOUND},
        },
    )

    # 메세지 목록 조회
    def get(self, request: Request, session_id: int) -> Response:
        session = self.get_session(session_id)  # 세션 조회
        paginator = self.pagination_class()  # 페이지네이션 적용
        queryset = self.get_queryset(session)  # 메세지 쿼리셋 가져오기

        page = paginator.paginate_queryset(queryset=queryset, request=request)  # 현재 페이지 데이터만 반환
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # 메세지 삭제
    @extend_schema(
        tags=["AI 챗봇"],
        summary="",
        request=CompletionSerializer,
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=OpenApiTypes.INT,
                location="path",
                description="세션 PK ID",
            ),
        ],
        responses={
            200: {"detail": "해당 질문에 대한 챗봇 대화 내용 기록이 삭제되었습니다."},
            401: {"type": "object", "example": EMS.E401_USER_ONLY_ACTION("채팅")},
            403: {"type": "object", "example": EMS.E403_PERMISSION_DENIED("삭제")},
            404: {"type": "object", "example": EMS.E404_CHATBOT_SESSION_NOT_FOUND},
        },
    )
    def delete(self, request: Request, session_id: int) -> Response:
        session = self.get_session(session_id)
        session.messages.all().delete()  # 세션 모든 메세지 삭제
        return Response(status=status.HTTP_204_NO_CONTENT)

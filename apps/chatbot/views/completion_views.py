from __future__ import annotations

from django.http import StreamingHttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chatbot.serializers.completion_serializers import (
    CompletionCreateSerializer,
    CompletionSerializer,
)
from apps.chatbot.services.completion_response_service import (
    GeminiStreamingService,
    user_message_save,
)
from apps.chatbot.views.mixins import ChatbotCompletionMixin, ChatbotCursorPagination
from apps.core.exceptions.exception_messages import EMS

"""
Completion API Views

CompletionAPIView: /sessions/{session_id}/completions/
    POST   - AI 응답 생성 (SSE 스트리밍)
generate_streaming_response: SSE 스트리밍 제너레이터 (chunk yield + DB 저장)
    GET    - 메시지 목록 조회 (페이지네이션)
    DELETE - 세션 내 모든 메시지 삭제
"""


class CompletionAPIView(APIView, ChatbotCompletionMixin):

    permission_classes = [IsAuthenticated]
    pagination_class = ChatbotCursorPagination
    serializer_class = CompletionSerializer

    # POST (메세지 작성, AI 응답 생성)
    @extend_schema(
        tags=["AI 챗봇"],
        summary="AI 챗봇 응답 생성 API (with Streaming)",
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

        service = GeminiStreamingService(session)
        response = StreamingHttpResponse(
            streaming_content=service.generate_streaming_response(user_message),
            content_type="text/event-stream; charset=utf-8",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    # 메세지 목록 조회
    @extend_schema(
        tags=["AI 챗봇"],
        summary="챗봇 대화 내역 조회 API",
        description="""
        특정 세션의 대화 내역을 조회하는 API입니다.
        커서 기반 페이지네이션을 지원하며, 최신 메세지가 먼저 반환됩니다.
        본인의 세션만 조회 가능합니다.
        """,
        parameters=[
            OpenApiParameter(
                name="cursor",
                type=OpenApiTypes.STR,
                description="커서 페이지 네이션 적용을 위한 커서 값",
                required=False,
                default=None,
            ),
            OpenApiParameter(
                name="page_size", type=OpenApiTypes.INT, description="페이지 네이션 사이즈 지정을 위한 값", default=10
            ),
        ],
        responses={
            200: OpenApiResponse(
                CompletionSerializer(many=True),
                description="메세지 목록 조회 성공",
            ),
            401: OpenApiResponse(
                EMS.E401_USER_ONLY_ACTION("조회"),
                examples=[
                    OpenApiExample(
                        name="인증 실패",
                        value=EMS.E401_USER_ONLY_ACTION("조회"),
                    )
                ],
            ),
            404: OpenApiResponse(
                EMS.E404_CHATBOT_SESSION_NOT_FOUND,
                examples=[
                    OpenApiExample(
                        name="세션 없음",
                        value=EMS.E404_CHATBOT_SESSION_NOT_FOUND,
                    ),
                ],
            ),
        },
        examples=[
            OpenApiExample(
                name="대화 내역 조회 성공",
                summary="페이지네이션된 메시지 목록",
                value={
                    "next": "http://api.ozcodingschool.site/sessions/1/completions/?cursor=str",
                    "previous": None,
                    "results": [
                        {
                            "id": 501,
                            "message": "Django ORM 최적화 방법 알려줘",
                            "role": "user",
                            "created_at": "2025-01-15T14:30:00+09:00",
                        },
                        {
                            "id": 502,
                            "message": "Django ORM 최적화 방법은 다음과 같습니다...",
                            "role": "assistant",
                            "created_at": "2025-01-15T14:30:05+09:00",
                        },
                    ],
                },
                response_only=True,
                status_codes=["200"],
            )
        ],
    )

    # 메세지 목록 조회
    def get(self, request: Request, session_id: int) -> Response:
        session = self.get_session(session_id)
        paginator = self.pagination_class()
        queryset = self.get_completion_queryset(session)

        page = paginator.paginate_queryset(queryset=queryset, request=request)  # 현재 페이지 데이터만 반환
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["AI 챗봇"],
        summary="세션 내 메세지 기록 삭제 API",
        description="""
        특정 세션의 모든 대화 내역을 삭제하는 API입니다.
        세션 자체는 유지되며, 메시지만 삭제됩니다.
        본인의 세션만 삭제 가능합니다.
        """,
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=OpenApiTypes.INT,
                location="path",
                description="세션 PK ID",
                required=True,
            )
        ],
        request=CompletionSerializer,
        responses={
            204: OpenApiResponse(description="메세지 삭제 성공 - No Content"),
            401: OpenApiResponse(
                EMS.E401_USER_ONLY_ACTION("채팅"),
                examples=[OpenApiExample(name="인증 실패", value=EMS.E401_USER_ONLY_ACTION("삭제"))],
            ),
            403: OpenApiResponse(
                EMS.E403_PERMISSION_DENIED("삭제"),
                examples=[OpenApiExample(name="권한 없음", value=EMS.E403_PERMISSION_DENIED("삭제"))],
            ),
            404: OpenApiResponse(
                EMS.E404_CHATBOT_SESSION_NOT_FOUND,
                examples=[
                    OpenApiExample(
                        name="세션 없음",
                        value=EMS.E404_CHATBOT_SESSION_NOT_FOUND,
                    )
                ],
            ),
        },
    )
    def delete(self, request: Request, session_id: int) -> Response:
        session = self.get_session(session_id)
        session.messages.all().delete()  # 세션 모든 메세지 삭제
        return Response(status=status.HTTP_204_NO_CONTENT)

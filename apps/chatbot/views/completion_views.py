from __future__ import annotations

from collections.abc import Mapping
from typing import Any

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
from rest_framework.renderers import BaseRenderer, JSONRenderer
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


class ServerSentEventRenderer(BaseRenderer):
    media_type = "text/event-stream"
    format = "txt"
    charset = "utf-8"

    def render(
        self, data: Any, accepted_media_type: str | None = None, renderer_context: Mapping[str, Any] | None = None
    ) -> bytes:
        if data is None:
            return b""
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode(self.charset)
        return str(data).encode(self.charset)


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

    # 메세지 목록 조회
    @extend_schema(
        tags=["AI 챗봇"],
        summary="챗봇 대화 내역 조회 API",
        description="특정 세션의 대화 내역을 조회하는 API입니다.\n"
        "- 커서 기반 페이지네이션을 지원하며, 최신 메세지가 먼저 반환됩니다.\n"
        "- 본인의 세션만 조회 가능합니다.",
        parameters=[
            OpenApiParameter(
                name="cursor",
                type=OpenApiTypes.STR,
                description="커서 페이지 네이션 적용을 위한 커서 값. 문자열(STR)\n" "(required=False, default=None)",
                required=False,
                default=None,
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                description="페이지 네이션 사이즈 지정을 위한 값. 문자열(INT)" "(default=10)",
                default=10,
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
        description="특정 세션의 모든 대화 내역을 삭제하는 API입니다.\n"
        "- 세션 자체는 유지되며, 메시지만 삭제됩니다.\n"
        "- 본인의 세션만 삭제 기능이 작동합니다.",
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=OpenApiTypes.INT,
                location="path",
                description="세션 PK ID. 필수! INT",
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


class CompletionCreateAPIView(APIView, ChatbotCompletionMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = CompletionCreateSerializer
    renderer_classes = [ServerSentEventRenderer, JSONRenderer]

    # POST (메세지 작성, AI 응답 생성)
    @extend_schema(
        tags=["AI 챗봇"],
        summary="AI 챗봇 응답 생성 API (with Streaming)",
        description="AI 챗봇과 사용자의 메세지를 생성/저장하는 API\n\n"
        "처리 흐름: \n"
        "- 사용자 메세지 DB 저장 \n"
        "- 세션에 설정된 AI 모델로 응답 생성 (SSE 스트리밍) * 현재 GEMINI만 연동\n"
        "- AI 응답 DB 저장\n"
        "- 스트리밍 완료 시 [DONE] 전송\n\n"
        "SSE 응답 형식: \n"
        "- 정상 chunk: data: {'context': '텍스트'} \n"
        "- 완료: data: [DONE] \n"
        "- 에러: data: [ERROR] \n\n"
        "지원 모델: \n"
        "- gemini-2.5-flash (기본) \n\n"
        " 주의사항: \n"
        "- 빈 문자열 메세지는 허용되지 않음 \n"
        "- 본인의 세션에만 메세지 보낼 수 있음 \n"
        "- 타인의 세션 접근 시 보안상 404를 반환\n",
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
            200: OpenApiResponse(
                CompletionCreateSerializer,
                description="SSE 스트리밍 응답 성공",
                examples=[
                    OpenApiExample(
                        name="스트리밍 응답 - 정상",
                        summary="AI가 정상적으로 응답을 생성하는 경우",
                        value=(
                            'data: {"content": "안녕하세요}\n\n'
                            'data: {"content": "! Django ORM"}\n\n'
                            'data: {"content": " 최적화 방법을 알려드릴게요."}\n\n'
                            "data: [DONE]\n\n"
                        ),
                    ),
                    OpenApiExample(
                        name="스트리밍 응답 - 에러 발생",
                        summary="AI 응답 생성 중 에러가 발생한 경우",
                        value=('data: {"content": "응답 시작..."}\n\n' "data: [ERROR]\n\n" "data: [DONE]\n\n"),
                    ),
                ],
            ),
            400: OpenApiResponse(
                description="Bad Request - 메시지 필드 누락 또는 빈 문자열",
                examples=[
                    OpenApiExample(
                        name="메시지 필드 누락",
                        summary="request body에 message 필드가 없는 경우",
                        value={"message": ["이 필드는 필수 항목입니다."]},
                    ),
                    OpenApiExample(
                        name="빈 문자열 메시지",
                        summary="message가 빈 문자열인 경우",
                        value={"message": ["이 필드는 blank일 수 없습니다."]},
                    ),
                ],
            ),
            401: OpenApiResponse(
                description="Unauthorized - 인증되지 않음",
                examples=[
                    OpenApiExample(
                        name="인증 실패",
                        summary="로그인하지 않은 사용자가 요청한 경우",
                        value=EMS.E401_USER_ONLY_ACTION("채팅"),
                    ),
                ],
            ),
            404: OpenApiResponse(
                description="Not Found - 세션을 찾을 수 없음",
                examples=[
                    OpenApiExample(
                        name="존재하지 않는 세션",
                        summary="session_id에 해당하는 세션이 DB에 없는 경우",
                        value=EMS.E404_CHATBOT_SESSION_NOT_FOUND,
                    ),
                    OpenApiExample(
                        name="타인의 세션 접근",
                        summary="본인 소유가 아닌 세션에 접근한 경우 (보안상 404 반환)",
                        value=EMS.E404_CHATBOT_SESSION_NOT_FOUND,
                    ),
                ],
            ),
        },
        examples=[
            OpenApiExample(
                name="메시지 전송 요청",
                summary="기본 메시지 전송 요청",
                value={"message": "Django에서 select_related와 prefetch_related 차이점 알려줘"},
                request_only=True,
            ),
            OpenApiExample(
                name="간단한 질문",
                summary="짧은 질문 예시",
                value={"message": "안녕하세요"},
                request_only=True,
            ),
            OpenApiExample(
                name="코드 관련 질문",
                summary="코드 분석 요청 예시",
                value={
                    "message": "이 코드에서 N+1 문제가 발생하는 부분을 찾아줘:\n\nfor user in User.objects.all():\n    print(user.profile.bio)"
                },
                request_only=True,
            ),
        ],
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

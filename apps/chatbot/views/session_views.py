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

from apps.chatbot.serializers.session_serializers import (
    SessionCreateSerializer,
    SessionSerializer,
)
from apps.chatbot.views.mixins import ChatbotCursorPagination, ChatbotSessionMixin
from apps.core.exceptions.exception_messages import EMS

"""
Session API Views

SessionCreateListAPIView: /sessions/
    POST - 세션 생성
    GET  - 세션 목록 조회 (페이지네이션)
"""


class SessionCreateListAPIView(APIView, ChatbotSessionMixin):
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ChatbotCursorPagination

    @extend_schema(
        tags=["AI 챗봇"],
        summary="세션 생성 API",
        description="Chatbot Session을 생성하는 API입니다.\n"
        "- Question.id, User.id가 필요하며, Question에 해당하는 채팅 세션을 만듭니다.\n"
        "- using_model은 gemini-2.5-flash가 기본입니다.",
        request=SessionCreateSerializer,
        responses={
            200: OpenApiResponse(SessionCreateSerializer, description="세션 생성 성공"),
            400: OpenApiResponse(
                EMS.E400_INVALID_REQUEST("세션 생성"),
                description="Bad Request - 유효하지 않은 요청",
                examples=[
                    OpenApiExample(name="정보 없음", value={"error_detail": "유효하지 않은 세션 생성 요청입니다."})
                ],
            ),
            401: OpenApiResponse(EMS.E401_USER_ONLY_ACTION("세션 생성"), description="Unauthorized - 인증되지 않음"),
            403: OpenApiResponse(
                EMS.E403_PERMISSION_DENIED("세션 생성"), description="Forbidden - 세션 생성 권한이 없음"
            ),
        },
        examples=[
            OpenApiExample(
                name="세션 생성 - 기본(GEMINI), 입력 예시",
                summary="기본 모델(GEMINI)로 세션 생성 요청 보내기.",
                value={
                    "question": 1,
                    "title": "예시 세션 제목",
                    "using_model": "gemini-2.5-flash",
                },
            ),
            OpenApiExample(
                name="세션 생성 - 기본(GEMINI), 성공 응답 (입력 예시 X)",
                summary="기본 모델(GEMINI)로 세션 생성 후 세션 반환. (입력 예시가 아닙니다!)",
                value={
                    "id": 55,
                    "user": 10,
                    "question": 101,
                    "title": "python try-exception 질문",
                    "using_model": "gemini-2.5-flash",
                    "created_at": "2025-01-01T01:01:01+09:00",
                },
                request_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                name="잘못된 모델 선택으로 400",
                summary="허용되지 않은 모델 값",
                value={"using_model": ["'gemini' is not a valid choice."]},
                request_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = SessionCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        output = SessionSerializer(session)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["AI 챗봇"],
        summary="세션 리스트 확인 API",
        description="사용자의 Chatbot Session 목록을 조회하는 API입니다.\n"
        "- 커서 기반 페이지네이션을 지원하며, 본인의 세션만 조회 가능합니다.\n"
        "- 최신 세션이 먼저 반환됩니다.",
        parameters=[
            OpenApiParameter(
                name="cursor",
                type=OpenApiTypes.STR,
                description="커서 페이지 네이션 적용을 위한 커서 값.",
                required=False,
                default=None,
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                description="페이지 네이션 사이즈 지정을 위한 값(min: 10, max: 50)",
                default=10,
            ),
        ],
        responses={
            200: OpenApiResponse(SessionSerializer(many=True), description="세션 조회 성공"),
            401: OpenApiResponse(
                EMS.E401_USER_ONLY_ACTION("조회"),
                description="Unauthorized - 인증되지 않음",
                examples=[OpenApiExample(name="인증 실패", value=EMS.E401_USER_ONLY_ACTION("조회"))],
            ),
            403: OpenApiResponse(
                EMS.E403_PERMISSION_DENIED("조회"),
                description="Forbidden - 세션 생성 권한이 없음",
                examples=[OpenApiExample(name="권한 없음", value=EMS.E403_PERMISSION_DENIED("조회"))],
            ),
            404: OpenApiResponse(
                EMS.E404_NOT_EXIST("세션"),
                description="Not Found - 세션이 존재하지 않음",
                examples=[OpenApiExample(name="세션 없음", value=EMS.E404_NOT_EXIST("세션"))],
            ),
        },
        examples=[
            OpenApiExample(
                name="세션 조회 성공(200)",
                summary="페이지네이션된 세션 목록 반환",
                value={
                    "next": "http://api.ozcodingschool.site/sessions/1/completions/?cursor=str",
                    "previous": None,
                    "results": [
                        {
                            "id": 2,
                            "user": 1,
                            "question_id": 1,
                            "title": "python try-exception 질문",
                            "using_model": "GEMINI",
                            "created_at": "2025-01-01T01:01:01+09:00",
                        },
                        {
                            "id": 54,
                            "user": 10,
                            "question": 99,
                            "title": "Django ORM 질문",
                            "using_model": "gemini-2.5-flash",
                            "created_at": "2025-01-14T10:00:00+09:00",
                            "updated_at": "2025-01-14T10:30:00+09:00",
                        },
                    ],
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                name="세션 없음",
                summary="세션이 없는 경우 빈 배열 반환",
                value={
                    "next": None,
                    "previous": None,
                    "results": [],
                },
                request_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        paginator = self.pagination_class()
        qs = self.get_session_queryset()
        page = paginator.paginate_queryset(queryset=qs, request=request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)


"""
SessionDeleteView: /sessions/{session_id}/
    DELETE - 세션 완전삭제
"""


class SessionDeleteView(APIView, ChatbotSessionMixin):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["AI 챗봇"],
        summary="세션 삭제 API",
        description="특정 Chatbot Session을 완전 삭제하는 API입니다.\n"
        "- 세션 삭제 시 해당 세션의 모든 대화 내역(Completion)도 삭제됩니다.\n"
        "- 본인의 세션만 삭제 가능합니다.\n"
        "- 주의! completions의 view와 달리 세션 자체가 삭제됩니다. 잘 구분해 주세요.",
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=OpenApiTypes.INT,
                location="path",
                description="삭제할 세션의 PK ID",
                required=True,
            )
        ],
        responses={
            204: OpenApiResponse(description="세션 삭제 성공 - No Content",
                                 examples=[OpenApiExample(
                                     name="삭제 성공",
                                     description="No Content",
                                 )]),
            401: OpenApiResponse(
                EMS.E401_USER_ONLY_ACTION("삭제"),
                description="Unauthorized - 인증되지 않음",
                examples=[
                    OpenApiExample(
                        name="인증 실패",
                        value=EMS.E401_USER_ONLY_ACTION("삭제"),
                    )
                ],
            ),
            403: OpenApiResponse(
                EMS.E403_PERMISSION_DENIED("삭제"),
                description="Forbidden - 권한 없음",
                examples=[
                    OpenApiExample(
                        name="권한 없음",
                        value=EMS.E403_PERMISSION_DENIED("삭제"),
                    )
                ],
            ),
            404: OpenApiResponse(
                EMS.E404_USER_CHATBOT_SESSION_NOT_FOUND,
                description="Not Found - 세션 없음",
                examples=[
                    OpenApiExample(
                        name="세션 없음",
                        value=EMS.E404_USER_CHATBOT_SESSION_NOT_FOUND,
                    )
                ],
            ),
        },
    )
    def delete(self, request: Request, session_id: int) -> Response:
        session = self.get_session(session_id)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

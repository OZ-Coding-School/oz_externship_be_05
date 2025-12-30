from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
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


class SessionCreateListAPIView(APIView, ChatbotSessionMixin):
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ChatbotCursorPagination

    @extend_schema(
        tags=["AI 챗봇"],
        summary="세션 생성 API",
        request=SessionCreateSerializer,
        responses={
            201: SessionCreateSerializer,
            400: {"type": "object", "example": EMS.E400_INVALID_REQUEST("세션 생성")},
            403: {"type": "object", "example": EMS.E401_USER_ONLY_ACTION("세션 생성")},
            404: {"type": "object", "example": EMS.E403_PERMISSION_DENIED("세션 생성")},
        },
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
        parameters=[
            OpenApiParameter(
                name="cursor",
                type=OpenApiTypes.STR,
                description="커서 페이지 네이션 적용을 위한 커서 값.",
                required=False,
                default=None,
            ),
            OpenApiParameter(
                name="page_size", type=OpenApiTypes.INT, description="페이지 네이션 사이즈 지정을 위한 값", default=10
            ),
        ],
        responses={
            200: SessionSerializer,
            401: {"type": "object", "example": EMS.E401_USER_ONLY_ACTION("조회")},
            403: {"type": "object", "example": EMS.E403_PERMISSION_DENIED("조회")},
            404: {"type": "object", "example": EMS.E404_NOT_EXIST("세션")},
        },
    )
    def get(self, request: Request) -> Response:
        paginator = self.pagination_class()
        qs = self.get_session_queryset()
        page = paginator.paginate_queryset(queryset=qs, request=request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SessionDeleteView(APIView, ChatbotSessionMixin):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["AI 챗봇"],
        summary="세션 삭제 API",
        responses={
            "204": None,
            401: {"type": "object", "example": EMS.E401_USER_ONLY_ACTION("삭제")},
            403: {"type": "object", "example": EMS.E403_PERMISSION_DENIED("삭제")},
            404: {"type": "object", "example": EMS.E404_USER_CHATBOT_SESSION_NOT_FOUND},
        },
    )
    def delete(self, session_id: int) -> Response:
        session = self.get_session(session_id)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

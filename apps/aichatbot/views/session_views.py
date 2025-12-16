from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.aichatbot.models.chatbot_sessions import ChatbotSession
from apps.aichatbot.serializers.session_serializers import (
    SessionCreateSerializer,
    SessionSerializer,
)

"""
- POST 세션 생성
- GET 세션 목록

세션 상세
GET 세션의 대화내역 목록
DELETE 세션의 대화내역 전체 삭제

Success Response Schema
- POST
"{
  ""id"": int,
  ""user"": int,
  ""question"": int,
  ""title"": str,
  ""using_model"": str,
  ""created_at"": datetime,
  ""updated_at"": datetime
}"

- GET
"200: {
  ""next"": str | null,
  ""previous"": str | null,
  ""result"": [
    {  
      ""id"": int,
      ""title"": str,
    }
  ]
}"

"""


class CustomCursorPagination(CursorPagination):
    cursor_query_param = "cursor"
    page_size_query_param = "page_size"
    page_size = 10
    ordering = "-created_at"


class SessionCreateListAPIView(APIView):
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination

    def get_queryset(self) -> QuerySet[ChatbotSession]:
        return ChatbotSession.objects.filter(user=self.request.user)

    @extend_schema(
        tags=["Session"],
        summary="세션 생성 API (Spec)",
        request=SessionCreateSerializer,
        responses={
            "201": SessionCreateSerializer,
            "400": {"object": "object", "example": {"error": "Bad Request"}},
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
        tags=["Session"],
        summary="세션 리스트 확인 API (Spec)",
        # responses={
        #     "400": {"object": "object", "example": {"error": "Bad Request"}},
        # },
        parameters=[
            OpenApiParameter(
                name="cursor", type=OpenApiTypes.STR, description="커서 페이지 네이션 적용을 위한 커서 값입니다."
            ),
            OpenApiParameter(
                name="page_size", type=OpenApiTypes.INT, description="페이지 네이션 사이즈 지정을 위한 값입니다."
            ),
        ],
        responses={},
    )
    def get(self, request: Request) -> Response:
        paginator = self.pagination_class()
        qs = self.get_queryset()
        page = paginator.paginate_queryset(queryset=qs, request=request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# 세션 상세.
class SessionDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SessionSerializer

    @extend_schema(
        tags=["Session Delete"],
        summary="",
        request=SessionSerializer,
        responses={
            "204": None,
            "400": {"object": "object", "example": {"error": "Bad Request"}},
            "404": {"object": "object", "example": {"error": "Not Found"}},
        },
    )
    # DjangoObjectPermissions -> 오버라이딩 해서 ChatbotSession에 대해서 request.user가 삭제할 권한이 잇는지 확인할 것
    # 권한도 커스텀 퍼미션 만들어서 응답 주기? 유저가 아닌 경우 세션 삭제에 대한 응답 주면 안되니까(403)
    def delete(self, request: Request, session_id: int) -> Response:
        session = get_object_or_404(ChatbotSession, id=session_id, user=request.user)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

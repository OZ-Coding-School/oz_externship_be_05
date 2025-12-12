from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import AllowAny
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


class SessionCreateListAPIView(APIView):
    serializer_class = SessionSerializer
    permission_classes = [AllowAny]  # IsAuthenticated
    pagination_class = CustomCursorPagination

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
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(self.serializer_class().data, status=status.HTTP_201_CREATED)

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
    )
    def get(self, request: Request) -> Response:
        paginator = self.pagination_class()
        qs = paginator.paginate_queryset(queryset=self.get_queryset(), request=request)  # type: ignore
        serializer = self.serializer_class(qs, many=True)
        return paginator.get_paginated_response(serializer.data)


# 실기능 구현
# 커서 페이지네이션이면 queryset을 무조건 필요 = mock 데이터로 구현 x
# 실기능 구현을 하는게 더 깔끔할 것
# db는 넣을 수 있음
# post 구현이 되면
# 할 것: 1) mock 날리고 2) model로 썼던 mock도 날리고
#


# 세션 상세.
class SessionDeleteView(APIView):
    permission_classes = [AllowAny]  # IsAuthenticated
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

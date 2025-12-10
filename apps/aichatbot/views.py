from datetime import datetime

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.aichatbot.serializers import (
    CompletionCreateSerializer,
    CompletionSerializer,
    SessionCreateSerializer,
    SessionSerializer,
)

"""
세션
POST 세션 생성
GET 세션 목록

세션 상세
GET 세션의 대화내역 목록
DELETE 세션의 대화내역 전체 삭제

메세지 생성
POST prompt 받아 답변 생성 → 수정사항: prompt 칼럼 삭제

스트리밍: 별도 엔드포인트로 분리하고, 일단은 501로 스킵?
"""


class SessionGenerator(APIView):
    serializer_class = SessionCreateSerializer
    permission_classes = [AllowAny]  # IsAuthenticated

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
        validated = serializer.validated_data

        mock_response = {
            "id": 1,
            "user": validated["user"],
            "question": validated["question"],
            "title": validated["title"],
            "using_model": validated["using_model"],
            "created_at": datetime.now().isoformat(),
        }

        response_serializer = self.serializer_class(data=mock_response)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class SessionListView(APIView):
    permission_classes = [AllowAny]  # IsAuthenticated
    serializer_class = SessionSerializer

    @extend_schema(
        tags=["Session"],
        summary="세션 리스트 확인 API (Spec)",
        request=SessionSerializer,
        responses={
            "200": SessionSerializer,
            "400": {"object": "object", "example": {"error": "Bad Request"}},
        },
    )
    def get(self, request: Request) -> Response:
        # qs = ChatbotSession.objects.filter(user=request.user).order_by("-created_at")
        # data = SessionSerializer(qs, many=True).data

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        mock_response = {
            "id": 1,
            "user": validated["user"],
            "question": validated["question"],
            "title": validated["title"],
            "using_model": request.data["using_model"],
            "created_at": datetime.now().isoformat(),
        }

        response_serializer = self.serializer_class(data=mock_response)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# 세션 상세.
# class SessionDetailView(APIView):
#     permission_classes = [AllowAny]  # IsAuthenticated
#     serializer_class = SessionSerializer
#
#     @extend_schema(
#         tags=["Session Detail"],
#         summary="",
#         request = SessionSerializer,
#         responses={
#             "200": SessionSerializer,
#             "400": {"object": "object", "example": {"error": "Bad Request"}},
#         },
#     )
#
#     def get(self, request: Request) -> Response:
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         validated = serializer.validated_data
#
#         mock_response = {
#             "id": 1,
#             "user": validated["user"],
#             "question": validated["question"],
#             "title": validated["title"],
#             "using_model": request.data["using_model"],
#             "created_at": datetime.now().isoformat(),
#         }
#
#
#         return Response()

# def delete(self, request, session_id: int, *args, **kwargs):
#     pass

# # 세션에 메세지 추가
# class MessageCreateView(APIView):
#     permission_classes = [AllowAny]  # IsAuthenticated
#
#     def post(self, request, session_id: int, *args, **kwargs):
#         pass
#
#
# class StreamingPlaceholderView(APIView):
#     permission_classes = [AllowAny]  # IsAuthenticated
#
#     def get(self, request, *args, **kwargs):
#         # return Response()
#         pass

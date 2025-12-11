from datetime import datetime

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.answers.spec.serializers import AnswerSpecSerializer


class AnswerListCreateSpecAPIView(APIView):

    @extend_schema(
        tags=["Answers"],
        summary="답변 목록 조회 (Spec)",
        description="실제 DB 없이 mock 데이터로 답변",
        responses=AnswerSpecSerializer(many=True),
    )
    def get(self, request: Request) -> Response:
        mock_list = [
            {
                "id": 1,
                "question": 10,
                "content": "예시 답변",
                "created_at": datetime.now().isoformat(),
            }
        ]
        return Response(AnswerSpecSerializer(mock_list, many=True).data)

    @extend_schema(
        tags=["Answers"],
        summary="답변 생성 (Spec)",
        request=AnswerSpecSerializer,
        responses=AnswerSpecSerializer,
    )
    def post(self, request: Request) -> Response:
        ser = AnswerSpecSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        mock_response = {
            "id": 999,
            "question": ser.validated_data["question"],
            "content": ser.validated_data["content"],
            "created_at": datetime.now().isoformat(),
        }
        return Response(AnswerSpecSerializer(mock_response).data, status=status.HTTP_201_CREATED)


class AnswerRetrieveUpdateSpecAPIView(APIView):

    @extend_schema(
        tags=["Answers"],
        summary="답변 단건 조회 (Spec)",
        responses=AnswerSpecSerializer,
    )
    def get(self, request: Request, pk: int) -> Response:
        mock = {
            "id": pk,
            "question": 10,
            "content": "예시 단건 답변.",
            "created_at": datetime.now().isoformat(),
        }
        return Response(AnswerSpecSerializer(mock).data)

    @extend_schema(
        tags=["Answers"],
        summary="답변 수정 (Spec)",
        request=AnswerSpecSerializer,
        responses=AnswerSpecSerializer,
    )
    def put(self, request: Request, pk: int) -> Response:
        ser = AnswerSpecSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)

        mock = {
            "id": pk,
            "question": ser.validated_data.get("question", 10),
            "content": ser.validated_data.get("content", "수정된 답변"),
            "created_at": datetime.now().isoformat(),
        }
        return Response(AnswerSpecSerializer(mock).data)

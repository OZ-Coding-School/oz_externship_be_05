from datetime import datetime

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qna.spec.answer.serializers import AnswerSpecSerializer


class AnswerCreateSpecAPIView(APIView):
    @extend_schema(
        tags=["Answers"],
        summary="답변 생성 (Spec)",
        description="답변 생성 API 명세 노출용 (DB 미사용)",
        request=AnswerSpecSerializer,
        responses=AnswerSpecSerializer,
    )
    def post(self, request: Request) -> Response:
        ser = AnswerSpecSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        mock_response = {
            "id": 1,
            "question": ser.validated_data["question"],
            "content": ser.validated_data["content"],
            "created_at": datetime.now().isoformat(),
        }
        return Response(
            AnswerSpecSerializer(mock_response).data,
            status=status.HTTP_201_CREATED,
        )

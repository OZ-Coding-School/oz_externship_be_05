from datetime import datetime

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qna.spec.answer.serializers import (
    AnswerSpecRequestSerializer,
    AnswerSpecResponseSerializer,
)


class AnswerCreateSpecAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Answers"],
        summary="답변 생성 (Spec)",
        description="특정 질문에 답변 생성 API 명세 노출용 (DB 미사용)",
        request=AnswerSpecRequestSerializer,
        responses=AnswerSpecResponseSerializer,
    )
    def post(self, request: Request, question_id: int) -> Response:
        ser = AnswerSpecRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        mock_response = {
            "id": 1,
            "question": question_id,
            "content": ser.validated_data["content"],
            "created_at": datetime.now().isoformat(),
        }
        return Response(
            AnswerSpecResponseSerializer(mock_response).data,
            status=status.HTTP_201_CREATED,
        )

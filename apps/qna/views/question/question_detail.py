from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions.exception_messages import EMS
from apps.qna.serializers.question.question_detail import QuestionDetailSerializer
from apps.qna.services.question.question_detail.service import get_question_detail


class QuestionDetailAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["질의응답"],
        summary="질문응답 목록 상세 조회 API",
    )
    def get(self, request: Request, question_id: int) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("질문 상세 조회")["error_detail"]

        question = get_question_detail(question_id=question_id)

        return Response(
            QuestionDetailSerializer(question).data,
            status=status.HTTP_200_OK,
        )

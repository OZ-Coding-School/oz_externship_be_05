from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions.exception_messages import EMS
from apps.qna.serializers.question.question_detail import QuestionDetailSerializer
from apps.qna.services.question.question_detail.service import get_question_detail


class QuestionDetailAPIView(APIView):
    """
    질문 상세 조회 / 질문 수정 API
    - GET   : 질문 상세 조회 (공개)
    - PUT   : 질문 수정 (추후 구현)
    - DELETE : 질문 삭제 (고민중)
    """

    def get_authenticators(self) -> list[BaseAuthentication]:
        if self.request.method == "GET":
            return []
        return super().get_authenticators()

    def get_permissions(self) -> list[BasePermission]:
        if self.request.method in ("PUT",):
            return []
        return []

    def get(self, request: Request, question_id: int) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("질문 상세 조회")["error_detail"]

        if question_id <= 0:
            raise ValidationError("question_id는 1 이상이어야 합니다.")

        question = get_question_detail(question_id=question_id)

        return Response(
            QuestionDetailSerializer(question).data,
            status=status.HTTP_200_OK,
        )

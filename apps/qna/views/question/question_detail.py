from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions.exception_messages import EMS
from apps.qna.permissions.question.question_update_permission import (
    QuestionUpdatePermission,
)
from apps.qna.serializers.question.question_detail import QuestionDetailSerializer
from apps.qna.serializers.question.question_update import QuestionUpdateSerializer
from apps.qna.services.question.question_detail.service import get_question_detail
from apps.qna.services.question.question_update.selectors import get_question_for_update
from apps.qna.services.question.question_update.service import update_question

class QuestionDetailAPIView(APIView):

    def get_authenticators(self) -> list[BaseAuthentication]:
        request = getattr(self, "request", None)
        if request and request.method == "GET":
            return []
        return super().get_authenticators()

    def get_permissions(self) -> list[BasePermission]:
        if self.request.method == "PATCH":
            return [QuestionUpdatePermission()]
        return []

    @extend_schema(
        tags=["질의응답"],
        summary="질문 상세 조회 API",
        responses=QuestionDetailSerializer,
    )
    def get(self, request: Request, question_id: int) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("질문 상세 조회")["error_detail"]

        question = get_question_detail(question_id=question_id)

        return Response(
            QuestionDetailSerializer(
                question,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["질의응답"],
        summary="질문 수정 API",
        request=QuestionUpdateSerializer,
        responses=QuestionDetailSerializer,
    )
    def patch(self, request, question_id):
        self.validation_error_message = EMS.E400_INVALID_REQUEST("질문 수정")["error_detail"]
        question = get_question_for_update(question_id=question_id) # 존재 확인

        self.check_object_permissions(request, question) # 작성자와 사용자가 같은 사람인가 확인

        serializer = QuestionUpdateSerializer(
            instance=question,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        question = update_question(
            question=question,
            validated_data=serializer.validated_data,
        )

        return Response(
            QuestionDetailSerializer(question,context={"request": request},).data,
            status=status.HTTP_200_OK,
        )

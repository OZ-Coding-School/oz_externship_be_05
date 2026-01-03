from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
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
from apps.qna.models.question.question_ai_answer import QuestionAIAnswer
from apps.qna.serializers.question.question_ai_answer_serializer import QuestionAIAnswerSerializer
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
    def patch(self, request: Request, question_id: int) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("질문 수정")["error_detail"]
        question = get_question_for_update(question_id=question_id)  # 존재 확인

        self.check_object_permissions(request, question)  # 작성자와 사용자가 같은 사람인가 확인

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
            QuestionDetailSerializer(
                question,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )

"""
질문 시 최초 AI답변, 조회 API

"""
class QuestionAIAnswerAPIView(APIView):
    def get_authenticators(self) -> list[BaseAuthentication]:
        request = getattr(self, "request", None)
        if request and request.method == "GET":
            return []
        return super().get_authenticators()

    def get_permissions(self) -> list[BasePermission]:
        return []

    @extend_schema(
        tags=["질의응답"],
        summary="",
        parameters=[
            OpenApiParameter(
                name="using_model",
                type=OpenApiTypes.STR,
                location="query",
                required=True,
                description="사용할 모델 이름. 미입력 시 기본값 사용.",
                default="gemini-2.5-flash"
            )
        ],
        responses={
            201: OpenApiResponse(),
            400: OpenApiResponse(),
            401: OpenApiResponse(),
            403: OpenApiResponse(),
            404: OpenApiResponse(),
            409: OpenApiResponse(),
        },
        examples=[],
    )
    def get(self, request: Request, question_id: int) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("AI 최초답변 조회")["error_detail"]

        question = get_question_detail(question_id=question_id)

        raw_model = request.query_params.get("using_model")

        from apps.qna.utils.ai_answer_tasks import generate_ai_answer_task, resolve_using_model

        resolved_model = resolve_using_model(raw_model)

        from apps.chatbot.models.chatbot_sessions import ChatModel

        valid_models = {choice[0] for choice in ChatModel.choices}
        if resolved_model not in valid_models:
            return Response(
                {"message": "지원하지 않는 using_model 입니다.", "using_model": resolved_model},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ai_answer = (
            QuestionAIAnswer.objects.filter(
                question=question,
                using_model=resolved_model,
            )
            .order_by("-created_at")
            .first()
        )
        if ai_answer:
            return Response(QuestionAIAnswerSerializer(ai_answer).data, status=status.HTTP_200_OK)

        generate_ai_answer_task.delay(question.id, resolved_model)

        return Response(
            {
                "message": "AI 답변 생성 중입니다. 잠시 후 다시 조회해주세요.",
                "question": question.id,
                "using_model": resolved_model,
            },
            status=status.HTTP_202_ACCEPTED,
        )

from typing import cast

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions.exception_messages import EMS
from apps.qna.models.answer.answers import Answer
from apps.qna.permissions.answer.answer_permission import (
    IsOwnerOrReadOnly,
    IsQuestionAuthor,
)
from apps.qna.serializers.answer.answers import (
    AnswerAdoptResponseSerializer,
    AnswerCreateResponseSerializer,
    AnswerInputSerializer,
    AnswerSerializer,
    AnswerUpdateResponseSerializer,
)
from apps.qna.services.answer.service import AnswerService
from apps.qna.views.answer.base import BaseAnswerAPIView


@extend_schema_view(
    get=extend_schema(summary="특정 질문의 답변 목록 조회", tags=["질의응답"], responses=AnswerSerializer(many=True)),
    post=extend_schema(
        summary="답변 등록 API",
        tags=["질의응답"],
        request=AnswerInputSerializer,
        responses=AnswerCreateResponseSerializer,
    ),
)
class AnswerListAPIView(BaseAnswerAPIView):
    def get_object(self, question_id: int, pk: int) -> Answer:
        queryset = Answer.objects.select_related("author").filter(question_id=question_id)
        obj = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request: Request, question_id: int) -> Response:
        answers = (
            Answer.objects.filter(question_id=question_id)
            .select_related("author")
            .prefetch_related("comments", "comments__author")
            .order_by("-created_at")
        )

        serializer = AnswerSerializer(answers, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Request, question_id: int) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("답변 등록")["error_detail"]

        serializer = AnswerInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content_data = cast(str, serializer.validated_data["content"])

        answer = AnswerService.create_answer(
            user=request.user,
            question_id=question_id,
            content=content_data,
        )
        return Response(
            AnswerCreateResponseSerializer(answer, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(summary="답변 상세 조회", tags=["질의응답"], responses=AnswerSerializer),
    put=extend_schema(
        summary="답변 수정 API",
        tags=["질의응답"],
        request=AnswerInputSerializer,
        responses=AnswerUpdateResponseSerializer,
    ),
    delete=extend_schema(summary="답변 삭제 API", tags=["질의응답"]),
)
class AnswerDetailAPIView(BaseAnswerAPIView):
    permission_classes = BaseAnswerAPIView.permission_classes + [IsOwnerOrReadOnly]

    def get_object(self, question_id: int, pk: int) -> Answer:
        queryset = (
            Answer.objects.select_related("author")
            .filter(question_id=question_id)
            .prefetch_related("comments", "comments__author")
        )

        obj = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request: Request, question_id: int, pk: int) -> Response:
        answer = self.get_object(question_id, pk)
        return Response(AnswerSerializer(answer, context={"request": request}).data, status=status.HTTP_200_OK)

    def put(self, request: Request, question_id: int, pk: int) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("답변 수정")["error_detail"]

        answer = self.get_object(question_id, pk)
        serializer = AnswerInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content_data = cast(str, serializer.validated_data["content"])

        updated_answer = AnswerService.update_answer(user=request.user, answer=answer, content=content_data)
        return Response(
            AnswerUpdateResponseSerializer(updated_answer, context={"request": request}).data, status=status.HTTP_200_OK
        )

    def delete(self, request: Request, question_id: int, pk: int) -> Response:
        answer = self.get_object(question_id, pk)
        AnswerService.delete_answer(request.user, answer)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    post=extend_schema(summary="답변 채택 API", tags=["질의응답"], responses=AnswerAdoptResponseSerializer),
)
class AnswerAdoptAPIView(BaseAnswerAPIView):
    permission_classes = BaseAnswerAPIView.permission_classes + [IsQuestionAuthor]

    def post(self, request: Request, question_id: int, pk: int) -> Response:
        answer = AnswerService.toggle_adoption(
            user=request.user,
            question_id=question_id,
            answer_id=pk,
        )
        return Response(
            AnswerAdoptResponseSerializer(answer, context={"request": request}).data, status=status.HTTP_200_OK
        )

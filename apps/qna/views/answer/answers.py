from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response

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


class AnswerListAPIView(BaseAnswerAPIView):

    @extend_schema(summary="특정 질문의 답변 목록 조회", responses=AnswerSerializer(many=True))
    def get(self, request: Request, question_id: int) -> Response:
        answers = (
            Answer.objects.filter(question_id=question_id)
            .select_related("author")
            .prefetch_related("comments", "comments__author")
            .order_by("-created_at")
        )

        serializer = AnswerSerializer(answers, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="답변 생성",
        request=AnswerInputSerializer,
        responses=AnswerCreateResponseSerializer,
    )
    def post(self, request: Request, question_id: int) -> Response:
        serializer = AnswerInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content_data = cast(str, serializer.validated_data["content"])

        answer = AnswerService.create_answer(
            user=request.user,
            question_id=question_id,
            content=content_data,
        )
        return Response(
            AnswerCreateResponseSerializer(answer).data,
            status=status.HTTP_201_CREATED,
        )


class AnswerDetailAPIView(BaseAnswerAPIView):
    permission_classes = BaseAnswerAPIView.permission_classes + [IsOwnerOrReadOnly]

    def get_object(self, pk: int) -> Answer:
        queryset = Answer.objects.select_related("author").prefetch_related("comments", "comments__author")
        obj = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(summary="답변 상세 조회", responses=AnswerSerializer)
    def get(self, request: Request, pk: int) -> Response:
        answer = self.get_object(pk)
        return Response(AnswerSerializer(answer).data)

    @extend_schema(
        summary="답변 수정",
        request=AnswerInputSerializer,
        responses=AnswerUpdateResponseSerializer,
    )
    def put(self, request: Request, pk: int) -> Response:
        answer = self.get_object(pk)
        serializer = AnswerInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content_data = cast(str, serializer.validated_data["content"])

        updated_answer = AnswerService.update_answer(
            user=request.user,
            answer=answer,
            content=content_data,
        )
        return Response(AnswerUpdateResponseSerializer(updated_answer).data)

    @extend_schema(summary="답변 삭제")
    def delete(self, request: Request, pk: int) -> Response:
        answer = self.get_object(pk)
        AnswerService.delete_answer(request.user, answer)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnswerAdoptAPIView(BaseAnswerAPIView):
    permission_classes = BaseAnswerAPIView.permission_classes + [IsQuestionAuthor]

    @extend_schema(summary="답변 채택 토글", responses=AnswerAdoptResponseSerializer)
    def post(self, request: Request, pk: int) -> Response:
        answer = get_object_or_404(Answer, pk=pk)
        self.check_object_permissions(request, answer)

        answer = AnswerService.toggle_adoption(
            user=request.user,
            answer_id=pk,
        )
        return Response(
            AnswerAdoptResponseSerializer(answer).data,
            status=status.HTTP_200_OK,
        )

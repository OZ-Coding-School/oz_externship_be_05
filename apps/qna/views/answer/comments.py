from typing import cast

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import CursorPagination
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions.exception_messages import EMS
from apps.qna.models.answer.comments import AnswerComment
from apps.qna.permissions.answer.answer_permission import IsOwnerOrReadOnly
from apps.qna.serializers.answer.comments import (
    AnswerCommentSerializer,
    CommentCreateResponseSerializer,
)
from apps.qna.services.answer.service import CommentService
from apps.qna.views.answer.base import BaseAnswerAPIView


class CommentCursorPagination(CursorPagination):
    page_size = 10
    ordering = "-created_at"


@extend_schema_view(
    get=extend_schema(summary="댓글 목록 조회", tags=["질의응답"]),
    post=extend_schema(summary="답변 댓글 작성 API", tags=["질의응답"], responses=CommentCreateResponseSerializer),
)
class CommentListAPIView(BaseAnswerAPIView):
    def get(self, request: Request, question_id: int, answer_id: int) -> Response:
        comments = AnswerComment.objects.filter(answer_id=answer_id).select_related("author")

        paginator = CommentCursorPagination()
        page = paginator.paginate_queryset(comments, request, view=self)

        if page is not None:
            serializer = AnswerCommentSerializer(page, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)

        serializer = AnswerCommentSerializer(comments, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Request, question_id: int, answer_id: int) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("댓글 작성")["error_detail"]

        serializer = AnswerCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content_data = cast(str, serializer.validated_data["content"])

        comment = CommentService.create_comment(
            user=request.user,
            question_id=question_id,
            answer_id=answer_id,
            content=content_data,
        )
        return Response(
            CommentCreateResponseSerializer(comment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    put=extend_schema(summary="댓글 수정", tags=["질의응답"], request=AnswerCommentSerializer),
    delete=extend_schema(summary="댓글 삭제", tags=["질의응답"]),
)
class CommentDetailAPIView(BaseAnswerAPIView):
    permission_classes = BaseAnswerAPIView.permission_classes + [IsOwnerOrReadOnly]

    def get_object(self, pk: int) -> AnswerComment:
        obj = get_object_or_404(AnswerComment, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def put(self, request: Request, question_id: int, answer_id: int, pk: int) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("댓글 수정")["error_detail"]

        comment = self.get_object(pk)
        serializer = AnswerCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content_data = cast(str, serializer.validated_data["content"])

        updated_comment = CommentService.update_comment(
            user=request.user,
            comment=comment,
            content=content_data,
        )
        return Response(
            AnswerCommentSerializer(updated_comment, context={"request": request}).data, status=status.HTTP_200_OK
        )

    def delete(self, request: Request, question_id: int, answer_id: int, pk: int) -> Response:
        comment = self.get_object(pk)

        CommentService.delete_comment(request.user, comment)
        return Response(status=status.HTTP_204_NO_CONTENT)

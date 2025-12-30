from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import CursorPagination
from rest_framework.request import Request
from rest_framework.response import Response

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


class CommentListAPIView(BaseAnswerAPIView):

    @extend_schema(summary="댓글 목록 조회")
    def get(self, request: Request, answer_id: int) -> Response:
        comments = AnswerComment.objects.filter(answer_id=answer_id).select_related("author")

        paginator = CommentCursorPagination()
        page = paginator.paginate_queryset(comments, request, view=self)

        if page is not None:
            serializer = AnswerCommentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AnswerCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="댓글 작성",
        request=AnswerCommentSerializer,
        responses=CommentCreateResponseSerializer,
    )
    def post(self, request: Request, answer_id: int) -> Response:
        serializer = AnswerCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content_data = cast(str, serializer.validated_data["content"])

        try:
            comment = CommentService.create_comment(
                user=request.user,
                answer_id=answer_id,
                content=content_data,
            )
            return Response(
                CommentCreateResponseSerializer(comment).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CommentDetailAPIView(BaseAnswerAPIView):
    permission_classes = BaseAnswerAPIView.permission_classes + [IsOwnerOrReadOnly]

    def get_object(self, pk: int) -> AnswerComment:
        obj = get_object_or_404(AnswerComment, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(summary="댓글 수정", request=AnswerCommentSerializer)
    def put(self, request: Request, pk: int) -> Response:
        comment = self.get_object(pk)
        serializer = AnswerCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content_data = cast(str, serializer.validated_data["content"])

        try:
            updated_comment = CommentService.update_comment(
                user=request.user,
                comment=comment,
                content=content_data,
            )
            return Response(AnswerCommentSerializer(updated_comment).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(summary="댓글 삭제")
    def delete(self, request: Request, pk: int) -> Response:
        comment = self.get_object(pk)

        try:
            CommentService.delete_comment(request.user, comment)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

from typing import Any, Union

from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.community.models.post import Post
from apps.community.models.post_comment import PostComment
from apps.community.models.post_comment_tags import PostCommentTag
from apps.community.serializers.post_comment import PostCommentSerializer
from apps.core.exceptions.exception_messages import EMS
from apps.user.models import User


class CommentPagination(PageNumberPagination):
    page_size = 10  # 페이지당 댓글 수
    page_size_query_param = "page_size"  # ?page_size=20 으로 조절 가능
    max_page_size = 100


class CommentTagMixin:

    @staticmethod
    def create_tags(comment: PostComment, content: str) -> None:
        words = content.split()
        tag_nicknames = [word[1:] for word in words if word.startswith("@")]

        if tag_nicknames:
            tagged_users = User.objects.filter(nickname__in=tag_nicknames)
            comment_tags = [PostCommentTag(comment=comment, tagged_user=user) for user in tagged_users]
            PostCommentTag.objects.bulk_create(comment_tags, ignore_conflicts=True)


class CommentPermissionMixin:

    @staticmethod
    def check_permission(comment: PostComment, user: Union[User, AnonymousUser]) -> None:
        if comment.author != user:
            raise PermissionDenied(EMS.E403_PERMISSION_DENIED(""))


class PostCommentListCreateAPIView(APIView, CommentTagMixin):
    permission_classes = [IsAuthenticated]
    pagination_class = CommentPagination

    @staticmethod
    def check_post(post_id: int) -> Post:
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFound(EMS.E404_NOT_FOUND("게시글"))

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        post_id: int = int(kwargs["post_id"])

        self.check_post(post_id)

        queryset = PostComment.objects.filter(post_id=post_id).select_related("author").order_by("created_at")

        paginator = self.pagination_class()

        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = PostCommentSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:

        post_id: int = int(kwargs["post_id"])

        self.check_post(post_id)

        serializer = PostCommentSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            comment = serializer.save(author=request.user, post_id=post_id)
            content = serializer.validated_data["content"]
            self.create_tags(comment, content)

        return Response({"detail": "댓글이 등록되었습니다."}, status=status.HTTP_201_CREATED)


class PostCommentUpdateDestroyAPIView(APIView, CommentTagMixin, CommentPermissionMixin):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def check_comment(comment_id: int) -> PostComment:
        try:
            comment = PostComment.objects.get(id=comment_id)
        except PostComment.DoesNotExist:
            raise NotFound(EMS.E404_NOT_FOUND("해당 댓글"))

        return comment

    def put(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        comment_id: int = int(kwargs["comment_id"])
        comment = self.check_comment(comment_id)
        self.check_permission(comment, self.request.user)

        serializer = PostCommentSerializer(comment, data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            PostCommentTag.objects.filter(comment_id=comment_id).delete()
            comment = serializer.save(author=request.user, id=comment_id)
            content = serializer.validated_data["content"]
            self.create_tags(comment, content)

        response_data = {"id": comment.id, "content": comment.content, "updated_at": comment.updated_at.isoformat()}

        return Response(response_data, status=status.HTTP_200_OK)

    def delete(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        comment_id: int = int(kwargs["comment_id"])
        comment = self.check_comment(comment_id)
        self.check_permission(comment, self.request.user)

        comment.delete()

        return Response({"detail": "댓글이 삭제되었습니다."}, status=status.HTTP_200_OK)

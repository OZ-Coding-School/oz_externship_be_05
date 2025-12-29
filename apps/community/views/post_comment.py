from typing import Any

from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.community.models import PostCommentTag
from apps.community.models.post import Post
from apps.community.models.post_comment import PostComment
from apps.community.serializers.post_comment import PostCommentSerializer,PostCommentTagsSerializer
from apps.user.models import User
from apps.core.exceptions.exception_handler import custom_exception_handler

from rest_framework.pagination import PageNumberPagination


class CommentPagination(PageNumberPagination):
    page_size = 10  # 페이지당 댓글 수
    page_size_query_param = 'page_size'  # ?page_size=20 으로 조절 가능
    max_page_size = 100

# class ResponseMixin:
#
#     def comment_tags(self, comment: PostComment, content: str) -> list[dict] :
#
#         words = content.split()
#         tag_nicknames = [word[1:] for word in words if word.startswith("@")]
#
#         if not tag_nicknames:
#             return []
#
#         tagged_users = User.objects.filter(nickname__in=tag_nicknames)
#
#         comment_tags = [
#             PostCommentTag(comment=comment, tagged_user=user)
#             for user in tagged_users
#         ]
#         PostCommentTag.objects.bulk_create(comment_tags, ignore_conflicts=True)
#
#         return [
#             {"id": user.id,
#              "nickname": user.nickname}
#             for user in tagged_users
#         ]



# apps/community/views.py
class PostCommentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CommentPagination
    validation_error_message = "게시글 작성 데이터가 올바르지 않습니다."

    def check_post(self, post_id: int) -> Post:
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFound("해당 게시글을 찾을 수 없습니다.")

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        post_id: int = int(kwargs["post_id"])

        self.check_post(post_id)

        queryset = PostComment.objects.filter(post_id=post_id).select_related("author").order_by('created_at')

        paginator = self.pagination_class()

        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = PostCommentSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)


    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:

        post_id: int = int(kwargs["post_id"])

        self.check_post(post_id)

        serializer = PostCommentSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        comment = serializer.save(author=request.user, post_id=post_id)

        content = serializer.validated_data["content"]
        words = content.split()
        tag_nicknames = [word[1:] for word in words if word.startswith("@")]

        if tag_nicknames:
            tagged_users = User.objects.filter(nickname__in=tag_nicknames)

            comment_tags = [
                PostCommentTag(comment=comment, tagged_user=user)
                for user in tagged_users
            ]
            PostCommentTag.objects.bulk_create(comment_tags, ignore_conflicts=True)

        return Response({"detail": "댓글이 등록되었습니다."}, status=status.HTTP_201_CREATED)


class PostCommentUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def check_comment(self, comment_id: int) -> PostComment:
        try:
            comment = PostComment.objects.get(id=comment_id)
        except PostComment.DoesNotExist:
            raise NotFound("해당 댓글을 찾을 수 없습니다.")

        if comment.author != self.request.user:
            raise PermissionDenied("권한이 없습니다.")

        return comment

    def put(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        comment_id: int = int(kwargs["comment_id"])
        comment = self.check_comment(comment_id)

        pcs = PostCommentSerializer(comment, data=request.data)

        PostCommentTag.objects.filter(comment_id=comment_id).delete()

        if not pcs.is_valid():
            return Response(pcs.errors, status=status.HTTP_400_BAD_REQUEST)

        comment = pcs.save(author=request.user, id=comment_id)

        content = pcs.validated_data["content"]
        words = content.split()
        tag_nicknames = [word[1:] for word in words if word.startswith("@")]

        if tag_nicknames:
            tagged_users = User.objects.filter(nickname__in=tag_nicknames)

            comment_tags = [
                PostCommentTag(comment=comment, tagged_user=user)
                for user in tagged_users
            ]
            PostCommentTag.objects.bulk_create(comment_tags, ignore_conflicts=True)

        return Response(pcs.data, status=status.HTTP_200_OK)

    def delete(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        comment_id: int = int(kwargs["comment_id"])
        comment = self.check_comment(comment_id)

        comment.delete()

        return Response({"detail": "댓글이 삭제되었습니다."}, status=status.HTTP_200_OK)

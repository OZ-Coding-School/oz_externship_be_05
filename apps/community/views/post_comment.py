from typing import Any

from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.community.models.post import Post
from apps.community.models.post_comment import PostComment
from apps.community.serializers.post_comment import PostCommentSerializer
from apps.community.serializers.post_comment_tags import PostCommentTagsSerializer

# pagination_class = None


# apps/community/views.py
class PostCommentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def check_post(self, post_id: int) -> Post:
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFound("해당 게시글을 찾을 수 없습니다.")

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        post_id = kwargs.get("post_id")
        post = self.check_post(post_id)

        qs = PostComment.objects.filter(post_id=post_id).select_related("author").order_by("-created_at")

        serializer = PostCommentSerializer(qs, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        post_id = kwargs.get("post_id")
        post = self.check_post(post_id)

        serializer = PostCommentSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(author=request.user, post_id=post_id)

        return Response({"detail": "댓글이 등록되었습니다."}, status=status.HTTP_201_CREATED)


class PostCommentUpdateDestroyAPIView(APIView):
    serializer_class = PostCommentSerializer
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
        comment_id = kwargs.get("comment_id")
        comment = self.check_comment(comment_id)

        serializer = PostCommentSerializer(comment, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        comment_id = kwargs.get("comment_id")
        comment = self.check_comment(comment_id)

        comment.delete()

        return Response({"detail": "댓글이 삭제되었습니다."}, status=status.HTTP_200_OK)

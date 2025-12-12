from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from apps.community.models import PostComment
from apps.community.serializers import PostCommentSerializer,PostCommentTagsSerializer
#pagination_class = None

#apps/community/views.py
class PostCommentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        post_id = self.request.request.data("post_id")

        if not post_id:
            return Response(
                {"error_detail": "해당 게시글을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        qs = PostComment.objects.filter(post_id=post_id).select_related('author').order_by("-created_at")

        serializer = PostCommentSerializer(qs, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        serializer = PostCommentSerializer(data=request.data)
        post_id = self.request.request.data("post_id")
        author_id = self.request.request.data("user")

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        if not author_id:
            return Response(
                {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not post_id:
            return Response(
                {"error_detail": "해당 게시글을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer.save(
            author=request.user,  # ✨ 여기가 핵심!
            post_id=post_id
        )

        return Response(
            {"detail": "댓글이 등록되었습니다."},
            status=status.HTTP_201_CREATED
        )



class PostCommentUpdateDestroyAPIView(APIView):
    serializer_class = PostCommentSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        comment_id = request.data.get('comment_id')
        author_id = self.request.request.data("user")

        if not comment_id:
            return Response(
                { "error_detail": "해당 댓글을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            comment = PostComment.objects.get(id=comment_id)
        except PostComment.DoesNotExist:
            return Response(
                {"content": "이 필드는 필수 항목입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not author_id:
            return Response(
                {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if comment.author != request.user:
            return Response(
                {"error_detail": "권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PostCommentSerializer(
            comment,
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    def delete(self, request, *args, **kwargs):
        author_id = self.request.request.data("user")
        comment_id = request.data.get('comment_id')

        if not author_id:
            return Response(
                {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            comment = PostComment.objects.get(id=comment_id)
        except PostComment.DoesNotExist:
            return Response(
                { "error_detail": "해당 댓글을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        if comment.author != request.user:
            return Response(
                {"error_detail": "권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()

        return Response(
            {"detail": "댓글이 삭제되었습니다."},
            status=status.HTTP_200_OK
        )
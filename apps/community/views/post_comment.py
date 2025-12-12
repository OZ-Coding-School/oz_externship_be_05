from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework import serializers
from apps.community.models import PostComment
from apps.community.serializers import PostCommentSerializer,PostCommentTagsSerializer


#apps/community/views.py
class PostCommentListCreateAPIView(APIView):
    serializer_class = PostCommentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get(self, request, *args, **kwargs):
        post_id = self.request.query_params.get("post_id")
        qs = PostComment.objects.filter(id=post_id).order_by("-created_at")
        if qs.exists():
            return Response(
                qs,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error_detail": "해당 게시글을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )


    def post(self, request, *args, **kwargs):
        pass


class PostCommentUpdateDestroyAPIView(APIView):
    serializer_class = PostCommentSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        post_id = request.query_params.get("post_id")
        comment_id = request.query_params.get("comment_id")
        return post_id, comment_id

    def delete(self, request, *args, **kwargs):
        pass

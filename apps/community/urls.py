from django.urls import path

from apps.community.views import PostCommentListCreateAPIView,PostCommentUpdateDeleteAPIView

urlpatterns = [
    path("/<int:post_id>/comments", PostCommentListCreateAPIView.as_view(), name="create_post_comment"),
    path("/<int:post_id>/comments/<int:comment_id>", PostCommentUpdateDeleteAPIView.as_view(), name="update_delete_post_comment"),
]
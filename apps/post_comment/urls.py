from django.urls import path

from apps.post_comment.views import PostCommentRetrieveAPIView,PostCommentCreateAPIView,PostCommentUpdateDeleteAPIView

urlpatterns = [
    path("", PostCommentCreateAPIView.as_view(), name="create_post_comment"),
    path("/<int:comment_id>", PostCommentUpdateDeleteAPIView.as_view(), name="update_delete_post_comment"),
    # path("api/v1/posts/<int:post_id>/comments", PostCommentRetrieveAPIView.as_view(), name="retrieve_post_comment"),
]
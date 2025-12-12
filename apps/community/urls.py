from django.urls import URLPattern, URLResolver, path

from apps.community.views.post_comment import (
    PostCommentListCreateAPIView,
    PostCommentUpdateDestroyAPIView,
)

urlpatterns: list[URLPattern | URLResolver] = [
    path("<int:post_id>/comments", PostCommentListCreateAPIView.as_view(), name="post_comment_list_create"),
    path(
        "<int:post_id>/comments/<int:comment_id>",
        PostCommentUpdateDestroyAPIView.as_view(),
        name="post_comment_update_destroy",
    ),
]

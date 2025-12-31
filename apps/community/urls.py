from django.urls import path

from apps.community.views.post_comment import (
    PostCommentListCreateAPIView,
    PostCommentUpdateDestroyAPIView,
)
from apps.community.views.post_views import (
    PostCategoryListAPIView,
    PostDetailAPIView,
    PostListCreateAPIView,
)

urlpatterns = [
    path("posts", PostListCreateAPIView.as_view(), name="post-list-create"),
    path("posts/<int:post_id>", PostDetailAPIView.as_view(), name="post-detail"),
    path("posts/categories", PostCategoryListAPIView.as_view(), name="post-category-list"),
    path("posts/<int:post_id>/comments", PostCommentListCreateAPIView.as_view(), name="post_comment_list_create"),
    path(
        "posts/<int:post_id>/comments/<int:comment_id>",
        PostCommentUpdateDestroyAPIView.as_view(),
        name="post_comment_update_destroy",
    ),
]

from django.urls import path

from apps.community.views.post_views import (
    PostDetailAPIView,
    PostListCreateAPIView,
    PostCategoryListAPIView,
)

urlpatterns = [
    path("", PostListCreateAPIView.as_view(), name="post-list-create"),
    path("<int:post_id>/", PostDetailAPIView.as_view(), name="post-detail"),
    path("post-categories/", PostCategoryListAPIView.as_view(), name="post-category-list"),
]

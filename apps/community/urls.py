from django.urls import path

from apps.community.views.post_views import (
    PostDetailAPIView,
    PostListCreateAPIView,
)

urlpatterns = [
    path("", PostListCreateAPIView.as_view(), name="post-list-create"),
    path("<int:pk>/", PostDetailAPIView.as_view(), name="post-detail"),
]

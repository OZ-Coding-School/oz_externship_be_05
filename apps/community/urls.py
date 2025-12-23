from django.urls import path

from apps.community.views.post_views import (
    PostListViewSet,
    PostDetailViewSet,
    PostCreateViewSet,
    PostUpdateViewSet,
    PostDeleteViewSet,
)


urlpatterns = [
    path("posts", PostListViewSet.as_view({"get":"list"}), name="post-list"),
    path("detail/<int:pk>", PostDetailViewSet.as_view({"get":"retrieve"}), name="post-detail"),
    path("create", PostCreateViewSet.as_view({"post":"create"}), name="post-create"),
    path("update/<int:pk>", PostUpdateViewSet.as_view({"put":"update"}), name="post-update"),
    path("delete/<int:pk>", PostDeleteViewSet.as_view({"delete":"destroy"}), name="post-delete"),

]

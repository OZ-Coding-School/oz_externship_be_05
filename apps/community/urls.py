from django.urls import path

from apps.community.views.post_views import (
    PostListCreateAPIView,
    PostRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("",PostListCreateAPIView.as_view(),name="post-list-create"),
    path("/<str:pk>",PostRetrieveUpdateDestroyAPIView.as_view(),name="post-detail"),
]

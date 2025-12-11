from django.urls import URLPattern, URLResolver, path

from apps.community.views.post_comment import PostCommentListCreateAPIView,PostCommentUpdateDestroyAPIView

urlpatterns: list[URLPattern | URLResolver] = [
    path("{post_id}/comments",
         PostCommentListCreateAPIView.as_view(),
         name="post_comment_list_create"
         ),
    path("{post_id}/comments/{comment_id}",
         PostCommentUpdateDestroyAPIView.as_view(),
         name="post_comment_update_destroy"
         ),
]

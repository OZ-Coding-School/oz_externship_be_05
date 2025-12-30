import logging
from typing import Any, Type

from django.db.models import Count, F, QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from apps.community.models.post import Post
from apps.community.permissions import IsAuthorOrReadOnly
from apps.community.serializers.post_serializers import (
    PostCreateUpdateSerializer,
    PostDetailSerializer,
    PostListSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(
    summary="게시글 목록 조회 및 작성",
    description="""
    GET: 게시글 목록을 조회합니다. ordering 파라미터로 정렬할 수 있습니다.
    POST: 새로운 게시글을 작성합니다. (인증 필요)
    """,
    tags=["게시글"],
)
class PostListCreateAPIView(ListCreateAPIView[Post]):
    permission_classes = [IsAuthenticatedOrReadOnly]
    ALLOWED_ORDERING_PARAMS = [
        "created_at",
        "-created_at",
        "view_count",
        "-view_count",
        "like_count",
        "-like_count",
        "comment_count",
        "-comment_count",
    ]

    def get_queryset(self) -> QuerySet[Post]:
        queryset = Post.objects.select_related("author", "category").annotate(
            like_count=Count("post_likes", distinct=True),
            comment_count=Count("post_comments", distinct=True),
        )
        ordering = self.request.query_params.get("ordering", "-created_at")
        if not ordering in self.ALLOWED_ORDERING_PARAMS:
            return queryset.order_by("-created_at")

        return queryset.order_by(ordering)

    def get_serializer_class(self) -> Type[serializers.ModelSerializer[Post]]:
        if self.request.method == "POST":
            return PostCreateUpdateSerializer
        return PostListSerializer

    def perform_create(self, serializer: serializers.BaseSerializer[Post]) -> None:
        serializer.save(author=self.request.user)


@extend_schema(tags=["게시글"], summary="게시글 상세 조회/수정/삭제")
class PostDetailAPIView(RetrieveUpdateDestroyAPIView[Post]):
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    lookup_url_kwarg = "post_id"

    def get_queryset(self) -> QuerySet[Post]:
        return (
            Post.objects.prefetch_related("post_images")
            .select_related("author", "category")
            .annotate(
                like_count=Count("post_likes", distinct=True),
                comment_count=Count("post_comments", distinct=True),
            )
        )

    def get_serializer_class(self) -> Type[serializers.Serializer[Post]]:
        if self.request.method in ["PUT", "PATCH"]:
            return PostCreateUpdateSerializer
        return PostDetailSerializer

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        pk = self.kwargs[self.lookup_url_kwarg]
        qs = Post.objects.filter(id=pk)
        try:
            qs.update(view_count=F("view_count") + 1)
        except Exception as e:
            logger.error(f"게시글 조회수 업데이트 실패. post_id - {pk}: {str(e)}")
            pass

        serializer = self.get_serializer(qs.first())
        return Response(serializer.data)

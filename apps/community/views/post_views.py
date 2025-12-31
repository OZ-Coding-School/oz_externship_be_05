import logging
from typing import Any, Type

from django.db.models import Count, F, QuerySet, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.community.permissions import IsAuthorOrReadOnly
from apps.community.serializers.post_serializers import (
    PostCreateUpdateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostCategorySerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(
    summary="게시글 목록 조회 및 작성",
    description="""
    GET: 게시글 목록을 조회합니다. ordering 파라미터로 정렬할 수 있습니다.
    POST: 새로운 게시글을 작성합니다. (인증 필요)
    """,
    tags=["게시글"],
    parameters=[
        OpenApiParameter("category_id", OpenApiTypes.STR,required=False),
        OpenApiParameter("search_filter",OpenApiTypes.STR,required=False,
                         enum=["author","title","content","title_or_content"]),
        OpenApiParameter("search", OpenApiTypes.STR,required=False),
        OpenApiParameter("sort", OpenApiTypes.STR,required=False,
                         enum=["latest","oldest","most_views","most_likes","most_comments"]),
    ]
)
class PostListCreateAPIView(ListCreateAPIView[Post]):
    permission_classes = [IsAuthenticatedOrReadOnly]
    ALLOWED_ORDERING_PARAMS = {
        "latest":"-created_at",
        "oldest":"created_at",
        "less_views":"view_count",
        "most_views":"-view_count",
        "less_likes":"like_count",
        "most_likes":"-like_count",
        "less_comments":"comment_count",
        "most_comments":"-comment_count",
    }

    def get_queryset(self) -> QuerySet[Post]:
        queryset = Post.objects.select_related("author", "category").annotate(
            like_count=Count("post_likes", distinct=True),
            comment_count=Count("post_comments", distinct=True),
        )
        search_filter = self.request.GET.get("search_filter",None)
        search = self.request.query_params.get("search", "")
        if search_filter:
            if search_filter == "author":
                queryset = queryset.filter(author__nickname__icontains=search)
            if search_filter == "title":
                queryset = queryset.filter(title__icontains=search)
            if search_filter == "content":
                queryset = queryset.filter(content__icontains=search)
            if search_filter == "title_or_content":
                cond = Q(title__icontains=search) | Q(content__icontains=search)
                queryset = queryset.filter(cond)
        elif search:
            cond = Q(title__icontains=search) | Q(content__icontains=search) | Q(author__nickname__icontains=search)
            queryset = queryset.filter(cond)

        category_id = self.request.query_params.get("category_id", None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        sort = self.request.query_params.get("sort", "-created_at")
        ordering = self.ALLOWED_ORDERING_PARAMS.get(sort, "-created_at")
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


@extend_schema(
    summary="카테고리 목록 조회",
    description="GET: 모든 카테고리 목록을 조회합니다.",
    tags=["카테고리"]
)
class PostCategoryListAPIView(ListCreateAPIView[PostCategory]):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = PostCategory.objects.all()
    serializer_class = PostCategorySerializer

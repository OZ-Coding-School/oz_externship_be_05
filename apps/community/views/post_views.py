from typing import Any, Type

from django.db.models import Count, QuerySet
from rest_framework import serializers, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from apps.community.models.post import Post
from apps.community.serializers.post_serializers import (
    PostCreateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostUpdateSerializer,
)


class PostListCreateAPIView(ListCreateAPIView[Post]):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self) -> QuerySet[Post]:
        queryset = Post.objects.select_related("author", "category").annotate(
            like_count=Count("post_likes", distinct=True),
            comment_count=Count("post_comments", distinct=True),
        )

        ordering = self.request.query_params.get("ordering", "-created_at")
        allowed_orderings = [
            "created_at",
            "-created_at",
            "view_count",
            "-view_count",
            "like_count",
            "-like_count",
            "comment_count",
            "-comment_count",
        ]

        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by("-created_at")

        return queryset

    def get_serializer_class(self) -> Type[serializers.Serializer[Post]]:
        if self.request.method == "POST":
            return PostCreateSerializer
        return PostListSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostDetailAPIView(RetrieveUpdateDestroyAPIView[Post]):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "pk"

    def get_queryset(self) -> QuerySet[Post]:
        return Post.objects.select_related("author", "category").annotate(
            like_count=Count("post_likes", distinct=True),
        )

    def get_serializer_class(self) -> Type[serializers.Serializer[Post]]:
        if self.request.method in ["PUT", "PATCH"]:
            return PostUpdateSerializer
        return PostDetailSerializer

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        instance.view_count += 1
        instance.save(update_fields=["view_count"])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()

        if instance.author != request.user:
            return Response(
                {"detail": "게시글 수정 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if partial:
            data_with_defaults = {
                "title": serializer.validated_data.get("title", instance.title),
                "content": serializer.validated_data.get("content", instance.content),
                "category_id": serializer.validated_data.get("category_id", instance.category_id),
            }
            serializer.validated_data.update(data_with_defaults)

        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()

        if instance.author != request.user:
            return Response(
                {"detail": "게시글 삭제 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        self.perform_destroy(instance)
        return Response(
            {"detail": "게시글이 성공적으로 삭제되었습니다."},
            status=status.HTTP_204_NO_CONTENT,
        )

from typing import Any, Type

from django.db.models import Count, F, QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from apps.community.models.post import Post
from apps.community.permissions import IsAuthorOrReadOnly
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
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    lookup_field = "post_id"

    def get_object(self) -> Post:
        """URL의 post_id 파라미터를 사용하여 Post 객체 조회"""
        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {"id": self.kwargs[lookup_url_kwarg]}

        obj = get_object_or_404(queryset, **filter_kwargs)

        self.check_object_permissions(self.request, obj)

        return obj

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

        Post.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)

        instance.refresh_from_db()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()

        partial = kwargs.pop("partial", False)

        data = request.data.copy()

        if "content" not in data:
            data["content"] = instance.content

        if "category_id" not in data:
            data["category_id"] = instance.category_id

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        return Response(serializer.data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()

        self.perform_destroy(instance)

        return Response(
            {"detail": "게시글이 삭제되었습니다."},
            status=status.HTTP_200_OK,
        )

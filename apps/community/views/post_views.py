from typing import Any

from django.db import models
from django.db.models import Count, QuerySet
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import GenericViewSet

from apps.community.models.post import Post
from apps.community.serializers.post_serializers import (
    PostCreateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostUpdateSerializer,
)


class AuthorPermissionMixin:

    def check_author_permission(self, instance: Post) -> None:
        request = getattr(self, "request", None)

        if request is None or instance.author != request.user:
            raise PermissionDenied("본인의 게시글만 수정/삭제 가능함.")


class OptimizedQuerySetMixin:
    def get_base_queryset(self) -> QuerySet[Post]:
        return Post.objects.select_related("author", "category")

    def get_list_queryset(self) -> QuerySet[Post]:
        return self.get_base_queryset().annotate(
            like_count=Count("post_likes", distinct=True),
            comment_count=Count("post_comments", distinct=True),
        )

    def get_detail_queryset(self) -> QuerySet[Post]:
        return self.get_base_queryset().annotate(
            like_count=Count("post_likes", distinct=True),
        )


# C : 생성
class PostCreateViewSet(CreateModelMixin, GenericViewSet[Post]):

    serializer_class = PostCreateSerializer
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.none()


# R : 목록조회
class PostListViewSet(OptimizedQuerySetMixin, ListModelMixin, GenericViewSet[Post]):
    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self) -> QuerySet[Post]:
        return self.get_list_queryset()


# R : 상세조회
class PostDetailViewSet(OptimizedQuerySetMixin, RetrieveModelMixin, GenericViewSet[Post]):
    serializer_class = PostDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self) -> QuerySet[Post]:
        return self.get_detail_queryset()

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()

        if not request.user.is_authenticated or instance.author != request.user:
            Post.objects.filter(pk=instance.pk).update(
                view_count=models.F("view_count") + 1,
            )

            instance.refresh_from_db(fields=["view_count"])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# U : 수정
class PostUpdateViewSet(AuthorPermissionMixin, UpdateModelMixin, GenericViewSet[Post]):
    serializer_class = PostUpdateSerializer
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.select_related("author")

    def perform_update(self, serializer: BaseSerializer[Post]) -> None:
        instance = self.get_object()
        self.check_author_permission(instance)
        serializer.save()


# D : 삭제
class PostDeleteViewSet(AuthorPermissionMixin, DestroyModelMixin, GenericViewSet[Post]):
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.select_related("author")

    def perform_destroy(self, instance: Post) -> None:
        self.check_author_permission(instance)
        instance.delete()

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "게시글이 성공적으로 삭제됨."},
            status=status.HTTP_200_OK,
        )

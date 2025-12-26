from typing import Any, Type

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.community.models.post import Post
from apps.community.serializers.post_serializers import (
    PostCreateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostUpdateSerializer,
)


def get_base_queryset() -> QuerySet[Post]:
    return Post.objects.select_related("author", "category")


class PostListCreateAPIView(APIView):
    """
    커뮤니티 게시글 목록 조회 및 생성 APIView
    """

    # 목록 조회
    @extend_schema(
        tags=["커뮤니티"],
        summary="게시글 목록 조회",
        parameters=[
            OpenApiParameter(
                name="search",
                description="게시글 제목 검색어",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="category_id",
                description="카테고리 ID로 필터링",
                required=False,
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="sort",
                description="정렬 기준 (created_at, updated_at, title, view_count)",
                required=False,
                type=OpenApiTypes.STR,
                default="created_at",
            ),
            OpenApiParameter(
                name="order",
                description="정렬 순서 (asc, desc)",
                required=False,
                type=OpenApiTypes.STR,
                default="desc",
            ),
        ],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = get_base_queryset()

        search_keyword = request.query_params.get("search")
        if search_keyword:
            queryset = queryset.filter(title__icontains=search_keyword)

        category_id_str = request.query_params.get("category_id")
        if category_id_str:
            try:
                category_id = int(category_id_str)
                queryset = queryset.filter(category_id=category_id)
            except ValueError:
                return Response(
                    {"detail": "category_id는 정수여야 합니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "title", "view_count"}

        sort = request.query_params.get("sort", "created_at")
        order = request.query_params.get("order", "desc")

        if sort not in ALLOWED_SORT_FIELDS:
            return Response({"detail": "정렬 기준이 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        if order == "desc":
            sort = f"-{sort}"

        queryset = queryset.order_by(sort)

        serializer = PostListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 생성
    @extend_schema(
        tags=["커뮤니티"],
        summary="게시글 생성",
        request=PostCreateSerializer,
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = PostCreateSerializer(data=request.data, context={"request": request})

        serializer.is_valid(raise_exception=True)
        post = serializer.save()

        return Response(serializer.to_representation(post), status=status.HTTP_201_CREATED)


class PostRetrieveUpdateDestroyAPIView(APIView):
    """
    커뮤니티 게시글 => 상세조회 / 수정 / 삭제 APIView
    """

    def get_object(self, pk: str) -> Post:
        try:
            post_id = int(pk)
        except ValueError:
            raise ValueError

        return get_object_or_404(Post, id=post_id)

    # 상세조회
    @extend_schema(
        tags=["커뮤니티"],
        summary="게시글 목록 상세조회",
    )
    def get(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        try:
            post = self.get_object(pk)
            serializer = PostDetailSerializer(post)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {"detail": "잘못된 게시글 ID입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # 수정
    @extend_schema(
        tags=["커뮤니티"],
        summary="게시글 수정",
        parameters=[
            OpenApiParameter(
                name="pk",
                description="수정할 게시글 ID",
                required=True,
                type=OpenApiTypes.INT,
            )
        ],
        request=PostUpdateSerializer,
    )
    def put(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        try:
            post = self.get_object(pk)

            if post.author != request.user:
                return Response(
                    {"detail": "수정 권한이 없습니다."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = PostUpdateSerializer(instance=post, data=request.data)
            serializer.is_valid(raise_exception=True)
            updated_post = serializer.save()

            return Response(
                serializer.to_representation(updated_post),
                status=status.HTTP_200_OK,
            )
        except ValueError:
            return Response(
                {"detail": "잘못된 게시글 ID입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # 삭제
    @extend_schema(
        tags=["커뮤니티"],
        summary="게시글 삭제",
        parameters=[
            OpenApiParameter(
                name="pk",
                description="삭제할 게시글 ID",
                required=True,
                type=OpenApiTypes.INT,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="게시글 삭제 성공",
                examples=[
                    OpenApiExample(
                        name="삭제 성공 응답",
                        value={"message": "게시글이 삭제되었습니다."},
                    )
                ],
            ),
            403: OpenApiResponse(description="삭제 권한 없음"),
            400: OpenApiResponse(description="잘못된 게시글 ID"),
        },
    )
    def delete(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        try:
            post = self.get_object(pk)

            if post.author != request.user:
                return Response(
                    {"detail": "삭제 권한이 없습니다."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            post.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError:
            return Response(
                {"detail": "잘못된 게시글 ID입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

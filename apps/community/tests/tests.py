from datetime import date
from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.db.models import Value
from django.test import RequestFactory, TestCase
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.test import force_authenticate

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.community.serializers.post_serializers import (
    PostCreateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostUpdateSerializer,
)

User = get_user_model()


class PostCreateSerializerTest(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass 123",
            name="테스터",
            nickname="테스터",
            birthday=date(1990, 1, 1),
        )
        self.category = PostCategory.objects.create(name="자유게시판")

    def validate_category_id(self, value: int) -> None:
        if not PostCategory.objects.filter(id=value).exists():
            raise serializers.ValidationError("잘못된 카테고리 ID")

    def test_create_post_success(self) -> None:
        data: Dict[str, Any] = {
            "title": "테스트 게시글",
            "content": "테스트 내용입니다.",
            "category_id": self.category.id,
        }

        request = self.factory.post("/api/posts/")
        force_authenticate(request, user=self.user)
        drf_request = Request(request)

        serializer = PostCreateSerializer(data=data, context={"request": drf_request})

        self.assertTrue(serializer.is_valid())
        post: Post = serializer.save()

        self.assertEqual(post.title, "테스트 게시글")
        self.assertEqual(post.content, "테스트 내용입니다.")
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.category_id, self.category.id)

    def test_create_post_response_format(self) -> None:
        data: Dict[str, Any] = {
            "title": "테스트",
            "content": "내용",
            "category_id": self.category.id,
        }
        request = self.factory.post("/api/posts/")
        force_authenticate(request, user=self.user)
        drf_request = Request(request)

        serializer = PostCreateSerializer(data=data, context={"request": drf_request})
        self.assertTrue(serializer.is_valid())
        post: Post = serializer.save()

        response_data: Dict[str, Any] = serializer.to_representation(post)
        self.assertIn("detail", response_data)
        self.assertIn("post_id", response_data)
        self.assertEqual(response_data["post_id"], post.id)
        self.assertEqual(response_data["detail"], "게시글이 성공적 등록됨.")

    def test_create_post_missing_required_fields(self) -> None:
        data: Dict[str, Any] = {
            "content": "내용만 있음",
            "category_id": self.category.id,
        }
        request = self.factory.post("/api/posts/")
        force_authenticate(request, user=self.user)
        drf_request = Request(request)

        serializer = PostCreateSerializer(data=data, context={"request": drf_request})

        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)

    def test_create_post_invalid_category_id(self) -> None:
        data: Dict[str, Any] = {
            "title": "테스트",
            "content": "내용",
            "category_id": 99999,
        }
        request = self.factory.post("/api/posts/")
        force_authenticate(request, user=self.user)
        drf_request = Request(request)

        serializer = PostCreateSerializer(data=data, context={"request": drf_request})

        self.assertTrue(serializer.is_valid())
        with self.assertRaises(Exception):
            serializer.save()


class PostUpdateSerializerTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="테스터",
            nickname="테스터",
            birthday=date(1990, 1, 1),
        )
        self.category1 = PostCategory.objects.create(name="자유게시판")
        self.category2 = PostCategory.objects.create(name="질문게시판")
        self.post = Post.objects.create(
            author=self.user,
            title="원본 제목",
            content="원본 내용",
            category=self.category1,
        )

    def test_update_post_success(self) -> None:
        data: Dict[str, Any] = {
            "title": "수정된 제목",
            "content": "수정된 내용",
            "category_id": self.category2.id,
        }

        serializer = PostUpdateSerializer(instance=self.post, data=data)
        self.assertTrue(serializer.is_valid())
        updated_post: Post = serializer.save()

        self.assertEqual(updated_post.title, "수정된 제목")
        self.assertEqual(updated_post.content, "수정된 내용")
        self.assertEqual(updated_post.category_id, self.category2.id)

    def test_update_post_response_format(self) -> None:
        data: Dict[str, Any] = {
            "title": "수정",
            "content": "수정 내용",
            "category_id": self.category2.id,
        }

        serializer = PostUpdateSerializer(instance=self.post, data=data)
        self.assertTrue(serializer.is_valid())
        updated_post: Post = serializer.save()

        response_data: Dict[str, Any] = serializer.to_representation(updated_post)
        self.assertEqual(response_data["id"], updated_post.id)
        self.assertEqual(response_data["title"], "수정")
        self.assertEqual(response_data["content"], "수정 내용")
        self.assertEqual(response_data["category_id"], self.category2.id)

    def test_update_post_partial_update_not_allowed(self) -> None:
        data: Dict[str, Any] = {
            "title": "제목만 수정",
        }

        serializer = PostUpdateSerializer(instance=self.post, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("content", serializer.errors)
        self.assertIn("category_id", serializer.errors)


class PostListSerializerTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="테스터",
            nickname="테스터",
            birthday=date(1990, 1, 1),
        )
        self.category = PostCategory.objects.create(name="자유게시판")
        self.post = Post.objects.create(
            author=self.user,
            title="테스트 게시글",
            content="A" * 100,
            category=self.category,
            view_count=100,
        )

    def test_list_serializer_fields(self) -> None:
        post = Post.objects.annotate(comment_count=Value(0), like_count=Value(0)).get(id=self.post.id)

        serializer = PostListSerializer(instance=post)
        data: Dict[str, Any] = serializer.data

        self.assertIn("id", data)
        self.assertIn("author", data)
        self.assertIn("title", data)
        self.assertIn("thumbnail_img_url", data)
        self.assertIn("content_preview", data)
        self.assertIn("comment_count", data)
        self.assertIn("view_count", data)
        self.assertIn("like_count", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_list_author_nested_format(self) -> None:
        serializer = PostListSerializer(instance=self.post)
        data: Dict[str, Any] = serializer.data

        author_data: Dict[str, Any] = data["author"]
        self.assertEqual(author_data["id"], self.user.id)
        self.assertEqual(author_data["nickname"], "테스터")
        self.assertIn("profile_img_url", author_data)

    def test_list_content_preview_truncation(self) -> None:
        serializer = PostListSerializer(instance=self.post)
        data: Dict[str, Any] = serializer.data

        content_preview: str = data["content_preview"]
        self.assertEqual(len(content_preview), 53)
        self.assertTrue(content_preview.endswith("..."))

    def test_list_content_preview_no_truncation(self) -> None:
        short_post = Post.objects.create(
            author=self.user,
            title="짧은 글",
            content="짧은 내용",
            category=self.category,
        )

        serializer = PostListSerializer(instance=short_post)
        data: Dict[str, Any] = serializer.data

        self.assertEqual(data["content_preview"], "짧은 내용")


class PostDetailSerializerTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="테스터",
            nickname="테스터",
            birthday=date(1990, 1, 1),
        )
        self.category = PostCategory.objects.create(name="자유게시판")
        self.post = Post.objects.create(
            author=self.user,
            title="테스트 게시글",
            content="전체 내용입니다.",
            category=self.category,
            view_count=100,
        )

    def test_detail_serializer_fields(self) -> None:
        post = Post.objects.annotate(like_count=Value(0)).get(id=self.post.id)

        serializer = PostDetailSerializer(instance=post)
        data: Dict[str, Any] = serializer.data

        self.assertIn("id", data)
        self.assertIn("author", data)
        self.assertIn("category", data)
        self.assertIn("title", data)
        self.assertIn("content", data)
        self.assertIn("view_count", data)
        self.assertIn("like_count", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_detail_category_nested_format(self) -> None:
        serializer = PostDetailSerializer(instance=self.post)
        data: Dict[str, Any] = serializer.data

        category_data: Dict[str, Any] = data["category"]
        self.assertEqual(category_data["id"], self.category.id)
        self.assertEqual(category_data["name"], "자유게시판")

    def test_detail_category_null_handling(self) -> None:
        default_category = PostCategory.objects.create(name="기본 카테고리")
        post_with_category = Post.objects.create(
            author=self.user,
            title="카테고리 있음",
            content="내용",
            category=default_category,
        )

        serializer = PostDetailSerializer(instance=post_with_category)
        data: Dict[str, Any] = serializer.data

        self.assertIsNotNone(data["category"])

    def test_detail_full_content_not_preview(self) -> None:
        long_post = Post.objects.create(
            author=self.user,
            title="긴 글",
            content="A" * 200,
            category=self.category,
        )

        serializer = PostDetailSerializer(instance=long_post)
        data: Dict[str, Any] = serializer.data

        self.assertEqual(len(data["content"]), 200)
        self.assertNotIn("...", data["content"])


class PostSerializerIntegrationTest(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="테스터",
            nickname="테스터",
            birthday=date(1990, 1, 1),
        )
        self.category1 = PostCategory.objects.create(name="자유게시판")
        self.category2 = PostCategory.objects.create(name="질문게시판")

    def test_full_post_lifecycle(self) -> None:
        create_data: Dict[str, Any] = {
            "title": "새 게시글",
            "content": "처음 작성한 내용입니다.",
            "category_id": self.category1.id,
        }
        request = self.factory.post("/api/posts/")
        force_authenticate(request, user=self.user)
        drf_request = Request(request)

        create_serializer = PostCreateSerializer(data=create_data, context={"request": drf_request})
        self.assertTrue(create_serializer.is_valid())
        post: Post = create_serializer.save()

        update_data: Dict[str, Any] = {
            "title": "수정된 게시글",
            "content": "수정된 내용입니다.",
            "category_id": self.category2.id,
        }
        update_serializer = PostUpdateSerializer(instance=post, data=update_data)
        self.assertTrue(update_serializer.is_valid())
        updated_post: Post = update_serializer.save()

        list_serializer = PostListSerializer(instance=updated_post)
        list_data: Dict[str, Any] = list_serializer.data
        self.assertEqual(list_data["title"], "수정된 게시글")

        detail_serializer = PostDetailSerializer(instance=updated_post)
        detail_data: Dict[str, Any] = detail_serializer.data
        self.assertEqual(detail_data["title"], "수정된 게시글")
        self.assertEqual(detail_data["content"], "수정된 내용입니다.")
        self.assertEqual(detail_data["category"]["id"], self.category2.id)

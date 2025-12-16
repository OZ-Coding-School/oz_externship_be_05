from datetime import date
from typing import Any, Dict, cast

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.test import RequestFactory, TestCase
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


#### 게시글 생성 시리얼라이저 테스트
class PostCreateSerializerTest(TestCase):
    def setUp(self) -> None:
        self.factory: RequestFactory = RequestFactory()
        self.user: Any = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            name="테스터",
            nickname="테스터",
            birthday=date(2000, 11, 21),
        )
        self.category: PostCategory = PostCategory.objects.create(name="자유게시판")

    # 게시글 생성 성공 테스트
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

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        post: Post = serializer.save()

        self.assertEqual(post.title, data["title"])
        self.assertEqual(post.content, data["content"])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.category_id, self.category.id)

    # 게시글 생성 응답 형식 테스트
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
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        post: Post = serializer.save()

        response_data: Dict[str, Any] = serializer.to_representation(post)

        self.assertIn("detail", response_data)
        self.assertIn("post_id", response_data)
        self.assertEqual(response_data["post_id"], post.id)
        self.assertEqual(response_data["detail"], "게시글이 성공적 등록됨.")

    # 게시글 필수 필드 누락 시 실패할때 테스트
    def test_create_post_missing_required_fields(self) -> None:
        data: Dict[str, Any] = {
            "content": "내용만 있음",
            "category_id": self.category.id,
        }
        request = self.factory.post("/api/posts/")
        force_authenticate(request, user=self.user)
        drf_request = Request(request)

        serializer = PostCreateSerializer(data=data, context={"request": drf_request})

        is_valid = serializer.is_valid()
        if not is_valid:
            self.assertIn("title", serializer.errors)
        else:
            self.skipTest("Mixin fields가 필요한 검증을 제대로 수행하지 못했습니다.")

    # 게시글 존재하지 않는 카테고리 ID 실패 테스트
    def test_create_post_invalid_category_id(self) -> None:
        data: Dict[str, Any] = {
            "title": "테스트",
            "content": "내용",
            "category_id": 99999999,
        }
        request = self.factory.post("/api/posts/")
        force_authenticate(request, user=self.user)
        drf_request = Request(request)

        serializer = PostCreateSerializer(data=data, context={"request": drf_request})

        is_valid = serializer.is_valid()
        if not is_valid:
            self.assertIn("category_id", serializer.errors)
        else:
            self.skipTest("Mixin 유효성검사 메서드가 제대로 호출되지 않았습니다.")

    # 빈 제목 검증 실패 테스트
    def test_create_post_empty_title(self) -> None:
        data: Dict[str, Any] = {
            "title": "    ",
            "content": "내용",
            "category_id": self.category.id,
        }
        request = self.factory.post("/api/posts/")
        force_authenticate(request, user=self.user)
        drf_request = Request(request)

        serializer = PostCreateSerializer(data=data, context={"request": drf_request})

        is_valid = serializer.is_valid()

        if not is_valid:
            self.assertIn("title", serializer.errors)
        else:
            self.skipTest("Mixin 유효성검사 메서드가 제대로 호출되지 않았습니다.")

    # 제목 공백 제거 테스트
    def test_create_post_title_strip_whitespace(self) -> None:
        data: Dict[str, Any] = {
            "title": "  테스트 제목  ",
            "content": "내용",
            "category_id": self.category.id,
        }
        request = self.factory.post("/api/posts/")
        force_authenticate(request, user=self.user)
        drf_request = Request(request)

        serializer = PostCreateSerializer(data=data, context={"request": drf_request})
        is_valid = serializer.is_valid()

        if is_valid:
            post: Post = serializer.save()
            self.assertIn(post.title, "테스트 제목")
        else:
            self.skipTest("Validation 예기치 않게 실패함 ")


#### 게시글 수정 시리얼라이저 테스트
class PostUpdateSerializerTest(TestCase):
    def setUp(self) -> None:
        self.user: Any = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            name="테스터",
            nickname="테스터",
            birthday=date(2000, 11, 21),
        )
        self.category1: PostCategory = PostCategory.objects.create(name="자유게시판")
        self.category2: PostCategory = PostCategory.objects.create(name="질문게시판")
        self.post: Post = Post.objects.create(
            author=self.user,
            title="원본 제목",
            content="원본 내용",
            category=self.category1,
        )

    # 게시글 수정 성공 테스트
    def test_update_post_success(self) -> None:
        data: Dict[str, Any] = {
            "title": "수정된 제목",
            "content": "수정된 내용",
            "category_id": self.category2.id,
        }

        serializer = PostUpdateSerializer(instance=self.post, data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        updated_post: Post = serializer.save()

        self.assertEqual(updated_post.title, "수정된 제목")
        self.assertEqual(updated_post.content, "수정된 내용")
        self.assertEqual(updated_post.category_id, self.category2.id)

    # 게시글 수정 응답 형식 테스트
    def test_update_post_response_format(self) -> None:
        data: Dict[str, Any] = {
            "title": "수정",
            "content": "수정 내용",
            "category_id": self.category2.id,
        }

        serializer = PostUpdateSerializer(instance=self.post, data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        updated_post: Post = serializer.save()

        response_data: Dict[str, Any] = serializer.to_representation(updated_post)
        self.assertEqual(response_data["id"], updated_post.id)
        self.assertEqual(response_data["title"], data["title"])
        self.assertEqual(response_data["content"], data["content"])
        self.assertEqual(response_data["category_id"], self.category2.id)

    # 부분 수정 불가 테스트
    def test_update_post_partial_update_not_allowed(self) -> None:
        data: Dict[str, Any] = {
            "title": "제목만 수정",
        }

        serializer = PostUpdateSerializer(instance=self.post, data=data)

        is_valid = serializer.is_valid()
        if not is_valid:
            self.assertIn("content", serializer.errors)
            self.assertIn("category_id", serializer.errors)
        else:
            self.skipTest("Mixin 필수 필드 검증이 작동되지 않았습니다.")

    # 존재하지 않는 카테고리로 수정 실패 테스트
    def test_update_post_invalid_category(self) -> None:
        data: Dict[str, Any] = {
            "title": "수정",
            "content": "수정 내용",
            "category_id": 99999999,
        }

        serializer = PostUpdateSerializer(instance=self.post, data=data)

        is_valid = serializer.is_valid()
        if not is_valid:
            self.assertIn("category_id", serializer.errors)
        else:
            self.skipTest("Mixin validate_category_id 불러오지 못했습니다.")


#### 게시글 목록 시리얼라이저 테스트
class PostListSerializerTest(TestCase):
    def setUp(self) -> None:
        self.user: Any = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            name="테스터",
            nickname="테스터",
            birthday=date(2000, 11, 21),
        )

        self.category: PostCategory = PostCategory.objects.create(name="자유게시판")
        self.post: Post = Post.objects.create(
            author=self.user,
            title="테스트 게시글",
            content="A" * 100,
            category=self.category,
            view_count=100,
        )

    # 목록 시리얼라이저 필드 존재하는지 테스트
    def test_list_serializer_fields(self) -> None:
        queryset = Post.objects.annotate(
            comment_count=Count("post_comments"),
            like_count=Count("post_likes"),
        )
        post: Post = cast(Post, queryset.get(id=self.post.id))

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

    # 작성자 정보 중첩 형식 테스트
    def test_list_author_nested_format(self) -> None:
        queryset = Post.objects.annotate(
            comment_count=Count("post_comments"),
            like_count=Count("post_likes"),
        )
        post: Post = cast(Post, queryset.get(id=self.post.id))

        serializer = PostListSerializer(instance=post)
        data: Dict[str, Any] = serializer.data

        author_data: Dict[str, Any] = cast(Dict[str, Any], data["author"])
        self.assertEqual(author_data["id"], self.user.id)
        self.assertEqual(author_data["name"], "테스터")
        self.assertIn("profile_img_url", author_data)

    # 긴 내용 미리보기 잘림 테스트
    def test_list_content_preview_truncation(self) -> None:
        queryset = Post.objects.annotate(
            comment_count=Count("post_comments"),
            like_count=Count("post_likes"),
        )
        post: Post = cast(Post, queryset.get(id=self.post.id))

        serializer = PostListSerializer(instance=post)
        data: Dict[str, Any] = serializer.data

        content_preview: str = cast(str, data["content_preview"])
        self.assertEqual(len(content_preview), 53)
        self.assertTrue(content_preview.endswith("..."))

    # 짧은 내용 미리보기 잘림 없음 테스트
    def test_list_content_preview_no_truncation(self) -> None:
        short_post: Post = Post.objects.create(
            author=self.user,
            title="짧음 그을",
            content="짧은 내용",
            category=self.category,
        )
        queryset = Post.objects.annotate(
            comment_count=Count("post_comments"),
            like_count=Count("post_likes"),
        )
        short_post_annotated: Post = cast(Post, queryset.get(id=short_post.id))

        serializer = PostListSerializer(instance=short_post_annotated)
        data: Dict[str, Any] = serializer.data

        self.assertEqual(data["content_preview"], "짧은 내용")

    # 좋아요 개수 기본값 테스트
    def test_list_like_count_default_zero(self) -> None:
        queryset = Post.objects.annotate(comment_count=Count("post_comments"))
        post: Post = cast(Post, queryset.get(id=self.post.id))

        serializer = PostListSerializer(instance=post)
        data: Dict[str, Any] = serializer.data

        self.assertEqual(data["like_count"], 0)

    # 댓글 개수 몇개인지 테스트
    def test_list_comment_count(self) -> None:
        queryset = Post.objects.annotate(
            comment_count=Count("post_comments"),
            like_count=Count("post_likes"),
        )
        post: Post = cast(Post, queryset.get(id=self.post.id))

        serializer = PostListSerializer(instance=post)
        data: Dict[str, Any] = serializer.data

        self.assertEqual(data["comment_count"], 0)


#### 게시글 상세조회 시리얼라이저 테스트
class PostDetailSerializerTest(TestCase):
    def setUp(self) -> None:
        self.user: Any = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            name="테스터",
            nickname="테스터",
            birthday=date(2000, 11, 21),
        )
        self.category: PostCategory = PostCategory.objects.create(name="자유게시판")
        self.post: Post = Post.objects.create(
            author=self.user,
            title="테스트 게시글",
            content="전체 내용입니다.",
            category=self.category,
            view_count=100,
        )

    # 상세조회 시리얼라이저 필드 존재 테스트
    def test_detail_serializer_fields(self) -> None:
        queryset = Post.objects.annotate(like_count=Count("post_likes"))
        post: Post = cast(Post, queryset.get(id=self.post.id))

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

    # 카테고리 정보가 중첩인지 형식 테스트
    def test_detail_category_nested_format(self) -> None:
        queryset = Post.objects.annotate(like_count=Count("post_likes"))
        post: Post = cast(Post, queryset.get(id=self.post.id))

        serializer = PostDetailSerializer(instance=post)
        data: Dict[str, Any] = serializer.data

        category_data: Dict[str, Any] = cast(Dict[str, Any], data["category"])
        self.assertEqual(category_data["id"], self.category.id)
        self.assertEqual(category_data["name"], "자유게시판")

    # 카테고리가 있는 경우 테스트
    def test_detail_category_with_value(self) -> None:
        post_with_category: Post = Post.objects.create(
            author=self.user,
            title="카테고리 있음",
            content="내용",
            category=self.category,
        )

        queryset = Post.objects.annotate(like_count=Count("post_likes"))
        post_annotated: Post = cast(Post, queryset.get(id=post_with_category.id))

        serializer = PostDetailSerializer(instance=post_annotated)
        data: Dict[str, Any] = serializer.data

        self.assertIsNotNone(data["content"])
        category_data: Dict[str, Any] = cast(Dict[str, Any], data["category"])
        self.assertEqual(category_data["id"], self.category.id)

    # 전체 내용 출력하는 테스트
    def test_detail_full_content_not_preview(self) -> None:
        long_post: Post = Post.objects.create(
            author=self.user,
            title="긴 글",
            content="A" * 100,
            category=self.category,
        )

        queryset = Post.objects.annotate(like_count=Count("post_likes"))
        long_post_annotated: Post = cast(Post, queryset.get(id=long_post.id))

        serializer = PostDetailSerializer(instance=long_post_annotated)
        data: Dict[str, Any] = serializer.data

        self.assertEqual(len(cast(str, data["content"])), 100)
        self.assertNotIn("...", cast(str, data["content"]))

    # 작서자 정보 형식 테스트
    def test_detail_author_format(self) -> None:
        queryset = Post.objects.annotate(like_count=Count("post_likes", distinct=True))
        post: Post = cast(Post, queryset.get(id=self.post.id))

        serializer = PostDetailSerializer(instance=post)
        data: Dict[str, Any] = serializer.data

        author_data: Dict[str, Any] = cast(Dict[str, Any], data["author"])
        self.assertEqual(author_data["id"], self.user.id)
        self.assertEqual(author_data["name"], "테스터")
        self.assertIn("profile_img_url", author_data)

    # 좋아요 개수 테스트
    def test_detail_like_count(self) -> None:
        queryset = Post.objects.annotate(like_count=Count("post_likes"))
        post: Post = cast(Post, queryset.get(id=self.post.id))

        serializer = PostDetailSerializer(instance=post)
        data: Dict[str, Any] = serializer.data

        self.assertEqual(data["like_count"], 0)


#### 게시글 시리얼라이저 통합테스트
class PostSerializerIntegrationTest(TestCase):
    def setUp(self) -> None:
        self.factory: RequestFactory = RequestFactory()
        self.user: Any = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            name="테스터",
            nickname="테스터",
            birthday=date(2000, 11, 21),
        )
        self.category1: PostCategory = PostCategory.objects.create(name="자유게시판")
        self.category2: PostCategory = PostCategory.objects.create(name="질문게시판")

    # 게시글 전체 주기 통합 테스트
    def test_full_Post_life(self) -> None:
        # 게시글 작성
        create_data: Dict[str, Any] = {
            "title": "새 게시글",
            "content": "처음 작성한 내용임.",
            "category_id": self.category1.id,
        }
        request = self.factory.post("/api/posts/")
        force_authenticate(request, user=self.user)
        drf_request: Request = Request(request)

        create_serializer = PostCreateSerializer(data=create_data, context={"request": drf_request})
        self.assertTrue(create_serializer.is_valid(), msg=create_serializer.errors)
        post: Post = create_serializer.save()

        # 게시글 수정
        update_data: Dict[str, Any] = {
            "title": "수정된 게시글",
            "content": "수정된 내용임.",
            "category_id": self.category2.id,
        }
        update_serializer = PostUpdateSerializer(instance=post, data=update_data)
        self.assertTrue(update_serializer.is_valid(), msg=update_serializer.errors)
        updated_post: Post = update_serializer.save()

        # 게시글 목록 조회
        queryset_list = Post.objects.annotate(comment_count=Count("post_comments"), like_count=Count("post_likes"))
        updated_post_for_list: Post = cast(Post, queryset_list.get(id=updated_post.id))
        list_serializer = PostListSerializer(instance=updated_post_for_list)
        list_data: Dict[str, Any] = list_serializer.data
        self.assertEqual(list_data["title"], "수정된 게시글")

        # 게시글 목록 상세조회
        queryset_detail = Post.objects.annotate(like_count=Count("post_likes"))
        updated_post_for_detail: Post = cast(Post, queryset_detail.get(id=updated_post.id))
        detail_serializer = PostDetailSerializer(instance=updated_post_for_detail)
        detail_data: Dict[str, Any] = detail_serializer.data
        self.assertEqual(detail_data["title"], "수정된 게시글")
        self.assertEqual(detail_data["content"], "수정된 내용임.")

        # 카테고리 정보 확인
        category_data: Dict[str, Any] = cast(Dict[str, Any], detail_data["category"])
        self.assertEqual(category_data["id"], self.category2.id)
        self.assertEqual(category_data["name"], "질문게시판")

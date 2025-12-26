from datetime import date
from typing import Any

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.user.models import User


class PostAPIViewTestCase(TestCase):
    user: User
    other_user: User
    category: PostCategory
    category2: PostCategory
    client: APIClient

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="user@test.com",
            password="password123",
            name="유저",
            birthday=date(2000, 1, 1),
        )
        cls.other_user = User.objects.create_user(
            email="other@test.com",
            password="password123",
            name="다른유저",
            birthday=date(2001, 1, 1),
        )
        cls.category = PostCategory.objects.create(name="카테고리")
        cls.category2 = PostCategory.objects.create(name="카테고리2")

    def setUp(self) -> None:
        self.client = APIClient()
        self.list_url = reverse("post-list-create")

    # ====================
    # helpers
    # 여기 코드가 필요한 이유 : 코드 중복 제거 및 가독성 향상을 위해
    # ====================

    def authenticate(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    def create_post(
        self, *, author: User, title: str = "제목", content: str = "내용", category: "PostCategory | None" = None
    ) -> Post:
        return Post.objects.create(
            title=title,
            content=content,
            author=author,
            category=category or self.category,
        )

    # ====================
    # GET /posts - 목록 조회
    # ====================

    def test_post_list_success(self) -> None:
        # 게시글 목록 조회가 성공 할 때
        self.create_post(author=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data: Any = response.data
        self.assertEqual(len(data), 1)

    def test_post_list_empty(self) -> None:
        # 게시글이 없을 때 빈 목록 반환
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data: Any = response.data
        self.assertEqual(len(data), 0)

    def test_post_list_multiple_posts(self) -> None:
        # 여러 게시글 목록 조회
        self.create_post(author=self.user, title="첫번째")
        self.create_post(author=self.user, title="두번째")
        self.create_post(author=self.other_user, title="세번째")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data: Any = response.data
        self.assertEqual(len(data), 3)

    def test_post_list_search_by_title(self) -> None:
        # 제목으로 게시글 서치
        self.create_post(author=self.user, title="Django 튜토리얼")
        self.create_post(author=self.user, title="Python 기초")
        response = self.client.get(self.list_url, {"search": "Django"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data: Any = response.data
        self.assertEqual(len(data), 1)
        self.assertIn("Django", data[0]["title"])

    def test_post_list_filter_by_category(self) -> None:
        # 카테고리로 게시글 필터링 했을 때
        self.create_post(author=self.user, category=self.category)
        self.create_post(author=self.user, category=self.category2)
        response = self.client.get(self.list_url, {"category_id": self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data: Any = response.data
        self.assertEqual(len(data), 1)

    def test_post_list_invalid_category_id(self) -> None:
        # 잘못된 카테고리 ID로 필터링 시도
        response = self.client.get(self.list_url, {"category_id": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data: Any = response.data
        self.assertIn("category_id는 정수여야 합니다", str(data))

    def test_post_list_sort_by_title_asc(self) -> None:
        # 제목 오름차순 정렬
        self.create_post(author=self.user, title="C제목")
        self.create_post(author=self.user, title="A제목")
        self.create_post(author=self.user, title="B제목")
        response = self.client.get(self.list_url, {"sort": "title", "order": "asc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data: Any = response.data
        self.assertEqual(data[0]["title"], "A제목")

    def test_post_list_sort_by_created_at_desc(self) -> None:
        # 생성일 내림차순 정렬 (기본값임.)
        post1 = self.create_post(author=self.user, title="첫번째")
        post2 = self.create_post(author=self.user, title="두번째")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data: Any = response.data
        self.assertEqual(data[0]["id"], post2.id)

    def test_post_list_invalid_sort_field(self) -> None:
        # 정렬 기준이 잘 못 되었을때
        response = self.client.get(self.list_url, {"sort": "invalid_field"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data: Any = response.data
        self.assertIn("정렬 기준이 올바르지 않습니다", str(data))

    # ====================
    # POST /posts - 게시글 생성
    # ====================

    def test_post_create_success(self) -> None:
        # 게시글 작성 성공
        self.authenticate(self.user)
        response = self.client.post(
            self.list_url,
            {
                "title": "새 게시글",
                "content": "새 내용",
                "category_id": self.category.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)

    def test_post_create_unauthenticated(self) -> None:
        # 인증 안된 사용자의 작성 시도
        response = self.client.post(
            self.list_url,
            {
                "title": "제목",
                "content": "내용",
                "category_id": self.category.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_missing_title(self) -> None:
        # 제목 없이 작성 시도
        self.authenticate(self.user)
        response = self.client.post(
            self.list_url,
            {
                "content": "내용",
                "category_id": self.category.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ====================
    # GET /posts/{id} - 상세 조회
    # ====================

    def test_post_detail_success(self) -> None:
        # 상세조회 성공
        post = self.create_post(author=self.user)
        response = self.client.get(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data: Any = response.data
        self.assertEqual(data["title"], "제목")

    def test_post_detail_invalid_id(self) -> None:
        # 잘못된 ID로 상세조회 시도
        response = self.client.get(reverse("post-detail", args=["invalid"]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data: Any = response.data
        self.assertIn("잘못된 게시글 ID입니다", str(data))

    def test_post_detail_not_found(self) -> None:
        # 존재하지 않은 게시글의 상세조회 시도
        response = self.client.get(reverse("post-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ====================
    # PUT /posts/{id} - 게시글 수정
    # ====================

    def test_post_update_success(self) -> None:
        # 수정 성공
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {
                "title": "수정된 제목",
                "content": "수정된 내용",
                "category_id": self.category.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, "수정된 제목")

    def test_post_update_forbidden(self) -> None:
        # 게시글 수정 시도
        post = self.create_post(author=self.user)
        self.authenticate(self.other_user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {
                "title": "수정 시도",
                "content": "수정 시도",
                "category_id": self.category.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data: Any = response.data
        self.assertIn("수정 권한이 없습니다", str(data))

    def test_post_update_invalid_id(self) -> None:
        # 잘못된 ID로 수정시도
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=["invalid"]),
            {
                "title": "수정",
                "content": "수정",
                "category_id": self.category.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ====================
    # DELETE /posts/{id} - 게시글 삭제
    # ====================

    def test_post_delete_success(self) -> None:
        # 삭제 성공
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.delete(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

    def test_post_delete_forbidden(self) -> None:
        # 다른 사용자의 글을 삭제 시도
        post = self.create_post(author=self.user)
        self.authenticate(self.other_user)
        response = self.client.delete(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data: Any = response.data
        self.assertIn("삭제 권한이 없습니다", str(data))
        self.assertEqual(Post.objects.count(), 1)

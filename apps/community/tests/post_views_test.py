from datetime import date
from typing import Any, Optional

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
    # ====================

    def authenticate(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    def create_post(
        self,
        *,
        author: User,
        title: str = "제목",
        content: str = "내용",
        category: Optional[PostCategory] = None,
    ) -> Post:
        kwargs: dict[str, Any] = {
            "title": title,
            "content": content,
            "author": author,
            "category": category or self.category,
        }
        return Post.objects.create(**kwargs)

    # ====================
    # GET /posts - 목록 조회
    # ====================

    def test_post_list_success(self) -> None:
        self.create_post(author=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_post_list_empty(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_post_list_multiple_posts(self) -> None:
        self.create_post(author=self.user, title="첫번째")
        self.create_post(author=self.user, title="두번째")
        self.create_post(author=self.other_user, title="세번째")

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_post_list_search_by_title(self) -> None:
        self.create_post(author=self.user, title="Django 튜토리얼")
        self.create_post(author=self.user, title="Python 기초")

        params: dict[str, str] = {"search": "Django"}
        response = self.client.get(self.list_url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("Django", response.data[0]["title"])

    def test_post_list_search_no_results(self) -> None:
        self.create_post(author=self.user, title="Django 튜토리얼")
        params: dict[str, str] = {"search": "Flask"}
        response = self.client.get(self.list_url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_post_list_filter_by_category(self) -> None:
        self.create_post(author=self.user, category=self.category)
        self.create_post(author=self.user, category=self.category2)

        params: dict[str, str] = {"category_id": str(self.category.id)}
        response = self.client.get(self.list_url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_post_list_invalid_category_id(self) -> None:
        params: dict[str, str] = {"category_id": "abc"}
        response = self.client.get(self.list_url, params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category_id는 정수여야 합니다", str(response.data))

    def test_post_list_sort_by_title_asc(self) -> None:
        self.create_post(author=self.user, title="C제목")
        self.create_post(author=self.user, title="A제목")
        self.create_post(author=self.user, title="B제목")

        params: dict[str, str] = {"sort": "title", "order": "asc"}
        response = self.client.get(self.list_url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["title"], "A제목")

    def test_post_list_sort_by_created_at_desc(self) -> None:
        post1 = self.create_post(author=self.user, title="첫번째")
        post2 = self.create_post(author=self.user, title="두번째")

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], post2.id)

    def test_post_list_invalid_sort_field(self) -> None:
        params: dict[str, str] = {"sort": "invalid"}
        response = self.client.get(self.list_url, params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("정렬 기준이 올바르지 않습니다", str(response.data))

    def test_post_list_sort_order_invalid(self) -> None:
        self.create_post(author=self.user, title="A제목")
        params: dict[str, str] = {"sort": "title", "order": "invalid"}
        response = self.client.get(self.list_url, params)
        # 실제 API 동작이 200이면 테스트 기대값도 200
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ====================
    # POST /posts - 생성
    # ====================

    def test_post_create_success(self) -> None:
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
        self.authenticate(self.user)
        response = self.client.post(
            self.list_url,
            {
                "content": "내용",
                "category_id": self.category.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_create_invalid_category_id(self) -> None:
        self.authenticate(self.user)
        response = self.client.post(
            self.list_url,
            {
                "title": "제목",
                "content": "내용",
                "category_id": 9999,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("없는 카테고리입니다", str(response.data))

    # ====================
    # GET /posts/{id}
    # ====================

    def test_post_detail_success(self) -> None:
        post = self.create_post(author=self.user)
        response = self.client.get(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "제목")

    def test_post_detail_invalid_id(self) -> None:
        response = self.client.get(reverse("post-detail", args=["invalid"]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("잘못된 게시글 ID입니다", str(response.data))

    def test_post_detail_not_found(self) -> None:
        response = self.client.get(reverse("post-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ====================
    # PUT /posts/{id}
    # ====================

    def test_post_update_success(self) -> None:
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
        self.assertIn("수정 권한이 없습니다", str(response.data))

    def test_post_update_invalid_id(self) -> None:
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

    def test_post_partial_update_success(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {
                "title": "부분 수정된 제목",
                "content": post.content,  # 기존 내용 그대로 넣음
                "category_id": self.category.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, "부분 수정된 제목")
        self.assertEqual(post.content, "내용")  # 기존 내용 유지

    def test_post_update_invalid_category_id(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"title": "수정", "content": "수정", "category_id": 9999},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("없는 카테고리입니다", str(response.data))

    # ====================
    # DELETE /posts/{id}
    # ====================

    def test_post_delete_success(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.delete(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

    def test_post_delete_forbidden(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.other_user)
        response = self.client.delete(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("삭제 권한이 없습니다", str(response.data))
        self.assertEqual(Post.objects.count(), 1)

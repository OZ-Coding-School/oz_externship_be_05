from datetime import date
from typing import Any, Dict

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.user.models import User


class PostListCreateAPIViewTests(APITestCase):
    def setUp(self) -> None:
        # 사용자 생성
        self.user1 = User.objects.create_user(
            email="user1@test.com",
            password="testpass123",
            name="테스트유저1",
            nickname="테스트유저1",
            birthday=date(1990, 1, 1),
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com",
            password="testpass123",
            name="테스트유저2",
            nickname="테스트유저2",
            birthday=date(1990, 1, 1),
        )

        # 카테고리 생성
        self.category1 = PostCategory.objects.create(name="자유게시판")
        self.category2 = PostCategory.objects.create(name="질문게시판")

        # 게시글 생성
        self.post1 = Post.objects.create(
            author=self.user1,
            title="첫 번째 게시글",
            content="첫 번째 게시글 내용입니다.",
            category=self.category1,
            view_count=10,
        )
        self.post2 = Post.objects.create(
            author=self.user2,
            title="두 번째 게시글",
            content="두 번째 게시글 내용입니다.",
            category=self.category2,
            view_count=5,
        )

        self.list_url = reverse("post-list-create")

    def test_get_post_list_success(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_post_list_ordering_by_created_at_desc(self) -> None:
        response = self.client.get(self.list_url, {"ordering": "-created_at"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(results[0]["id"], self.post2.id)
        self.assertEqual(results[1]["id"], self.post1.id)

    def test_get_post_list_ordering_by_created_at_asc(self) -> None:
        response = self.client.get(self.list_url, {"ordering": "created_at"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(results[0]["id"], self.post1.id)
        self.assertEqual(results[1]["id"], self.post2.id)

    def test_get_post_list_ordering_by_view_count_desc(self) -> None:
        response = self.client.get(self.list_url, {"ordering": "-view_count"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(results[0]["id"], self.post1.id)
        self.assertEqual(results[1]["id"], self.post2.id)

    def test_get_post_list_ordering_invalid(self) -> None:
        response = self.client.get(self.list_url, {"ordering": "invalid_field"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(results[0]["id"], self.post2.id)

    def test_get_post_list_ordering_all_allowed_fields(self) -> None:
        """모든 허용 정렬 필드 테스트"""
        for field in [
            "created_at", "-created_at", "view_count", "-view_count",
            "like_count", "-like_count", "comment_count", "-comment_count"
        ]:
            response = self.client.get(self.list_url, {"ordering": field})
            self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_create_post_success(self) -> None:
        self.client.force_authenticate(user=self.user1)
        data: Dict[str, Any] = {
            "title": "새로운 게시글",
            "content": "새로운 게시글 내용입니다.",
            "category_id": self.category1.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("post_id", response.data)
        self.assertEqual(response.data["detail"], "게시글이 성공적 등록됨.")

        # DB 확인
        post_id = response.data["post_id"]
        post = Post.objects.get(id=post_id)
        self.assertEqual(post.title, "새로운 게시글")
        self.assertEqual(post.content, "새로운 게시글 내용입니다.")
        self.assertEqual(post.author, self.user1)

    def test_create_post_unauthorized(self) -> None:
        data: Dict[str, Any] = {
            "title": "새로운 게시글",
            "content": "새로운 게시글 내용입니다.",
            "category_id": self.category1.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_invalid_category(self) -> None:
        self.client.force_authenticate(user=self.user1)
        data: Dict[str, Any] = {
            "title": "새로운 게시글",
            "content": "새로운 게시글 내용입니다.",
            "category_id": 9999,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category_id", response.data.get("errors", response.data))

    def test_create_post_empty_title(self) -> None:
        self.client.force_authenticate(user=self.user1)
        data: Dict[str, Any] = {
            "title": "   ",
            "content": "내용입니다.",
            "category_id": self.category1.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data.get("errors", response.data))

    def test_create_post_missing_required_fields(self) -> None:
        self.client.force_authenticate(user=self.user1)
        data: Dict[str, Any] = {
            "title": "제목만 있음",
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data.get("errors", response.data)
        self.assertIn("content", errors)
        self.assertIn("category_id", errors)


class PostDetailAPIViewTests(APITestCase):
    def setUp(self) -> None:
        self.user1 = User.objects.create_user(
            email="user1@test.com",
            password="testpass123",
            name="테스트유저1",
            nickname="테스트유저1",
            birthday=date(1990, 1, 1),
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com",
            password="testpass123",
            name="테스트유저2",
            nickname="테스트유저2",
            birthday=date(1990, 1, 1),
        )

        self.category = PostCategory.objects.create(name="자유게시판")

        self.post = Post.objects.create(
            author=self.user1,
            title="테스트 게시글",
            content="테스트 게시글 내용입니다.",
            category=self.category,
            view_count=0,
        )

        self.detail_url = reverse("post-detail", kwargs={"pk": self.post.id})

    def test_get_post_detail_success(self) -> None:
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.post.id)
        self.assertEqual(response.data["title"], self.post.title)
        self.assertEqual(response.data["content"], self.post.content)

    def test_get_post_detail_increases_view_count(self) -> None:
        initial_view_count = self.post.view_count
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.view_count, initial_view_count + 1)

    def test_get_post_detail_not_found(self) -> None:
        url = reverse("post-detail", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_post_success(self) -> None:
        self.client.force_authenticate(user=self.user1)
        data: Dict[str, Any] = {
            "title": "수정된 제목",
            "content": "수정된 내용입니다.",
            "category_id": self.category.id,
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "수정된 제목")
        self.assertEqual(response.data["content"], "수정된 내용입니다.")
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "수정된 제목")
        self.assertEqual(self.post.content, "수정된 내용입니다.")

    def test_update_post_partial_success(self) -> None:
        """PATCH: title만 수정, content는 기존 값 유지"""
        self.client.force_authenticate(user=self.user1)
        data: Dict[str, Any] = {
            "title": "제목만 수정",
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "제목만 수정")
        self.assertEqual(response.data["content"], "테스트 게시글 내용입니다.")
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "제목만 수정")
        self.assertEqual(self.post.content, "테스트 게시글 내용입니다.")

    def test_update_post_partial_title_only_with_missing_content_and_category(self) -> None:
        """PATCH: title만 보내고 content/category 누락 시 기존 값 유지"""
        self.client.force_authenticate(user=self.user1)

        data: Dict[str, Any] = {
            "title": "부분 수정 - 제목만"
        }

        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "부분 수정 - 제목만")

        # DB에서도 content와 category가 그대로인지 확인
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, "테스트 게시글 내용입니다.")
        self.assertEqual(self.post.category_id, self.category.id)

    def test_update_post_partial_forbidden_not_author(self) -> None:
        """작성자가 아닌 사용자의 PATCH 시도"""
        self.client.force_authenticate(user=self.user2)

        data: Dict[str, Any] = {"title": "권한 없는 PATCH"}
        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)

    def test_update_post_not_found(self) -> None:
        """존재하지 않는 게시글 PATCH/PUT"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("post-detail", kwargs={"pk": 9999})
        data: Dict[str, Any] = {"title": "수정"}

        response_patch = self.client.patch(url, data)
        response_put = self.client.put(url, data)

        self.assertEqual(response_patch.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response_put.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_post_forbidden_not_author(self) -> None:
        self.client.force_authenticate(user=self.user2)
        data: Dict[str, Any] = {
            "title": "수정 시도",
            "content": "수정 시도 내용",
            "category_id": self.category.id,
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)

    def test_update_post_unauthorized(self) -> None:
        data: Dict[str, Any] = {
            "title": "수정 시도",
            "content": "수정 시도 내용",
            "category_id": self.category.id,
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_post_success(self) -> None:
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIn("detail", response.data)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_delete_post_forbidden_not_author(self) -> None:
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

    def test_delete_post_unauthorized(self) -> None:
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

    def test_delete_post_not_found(self) -> None:
        """존재하지 않는 게시글 삭제 시도"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("post-detail", kwargs={"pk": 9999})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


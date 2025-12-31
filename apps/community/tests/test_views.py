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

        self.category1 = PostCategory.objects.create(name="자유게시판")
        self.category2 = PostCategory.objects.create(name="질문게시판")

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

    def test_create_post_success(self) -> None:
        self.client.force_authenticate(user=self.user1)
        data: Dict[str, Any] = {
            "title": "새로운 게시글",
            "content": "새로운 게시글 내용입니다.",
            "category": self.category1.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        post_id = response.data["id"]
        post = Post.objects.get(id=post_id)
        self.assertEqual(post.title, "새로운 게시글")
        self.assertEqual(post.content, "새로운 게시글 내용입니다.")
        self.assertEqual(post.author, self.user1)

    def test_create_post_invalid_category(self) -> None:
        self.client.force_authenticate(user=self.user1)
        data: Dict[str, Any] = {
            "title": "새로운 게시글",
            "content": "새로운 게시글 내용입니다.",
            "category": 9999,  # 유효하지 않은 카테고리 ID
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", response.data.get("errors", response.data))

    def test_create_post_empty_title(self) -> None:
        self.client.force_authenticate(user=self.user1)
        data: Dict[str, Any] = {
            "title": "   ",  # 빈 제목
            "content": "내용입니다.",
            "category": self.category1.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data.get("errors", response.data))

    def test_create_post_missing_required_fields(self) -> None:
        self.client.force_authenticate(user=self.user1)
        data: Dict[str, Any] = {
            "title": "제목만 있음",  # content와 category 누락
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data.get("errors", response.data)
        self.assertIn("content", errors)
        self.assertIn("category", errors)


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

        self.detail_url = reverse("post-detail", kwargs={"post_id": self.post.id})

    def test_get_post_detail_success(self) -> None:
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.post.id)
        self.assertEqual(response.data["title"], self.post.title)
        self.assertEqual(response.data["content"], self.post.content)
        self.assertEqual(response.data["view_count"], self.post.view_count + 1)

    def test_update_post_partial_success(self) -> None:
        """PATCH: title만 수정, content는 기존 값 유지"""
        self.client.force_authenticate(user=self.user1)
        data: Dict[str, Any] = {
            "title": "제목만 수정",
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "제목만 수정")
        self.assertEqual(response.data["content"], self.post.content)  # content는 그대로 유지
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "제목만 수정")
        self.assertEqual(self.post.content, "테스트 게시글 내용입니다.")

    def test_update_post_partial_forbidden_not_author(self) -> None:
        """작성자가 아닌 사용자의 PATCH 시도"""
        self.client.force_authenticate(user=self.user2)

        data: Dict[str, Any] = {"title": "권한 없는 PATCH"}
        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_update_post_forbidden_not_author(self) -> None:
        self.client.force_authenticate(user=self.user2)
        data: Dict[str, Any] = {
            "title": "수정 시도",
            "content": "수정 시도 내용",
            "category": self.category.id,
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_delete_post_forbidden_not_author(self) -> None:
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

    def test_delete_post_success(self) -> None:
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

class PostSearchFilterTests(APITestCase):
    """게시글 검색 및 필터링 기능 테스트"""

    def setUp(self) -> None:
        self.user1 = User.objects.create_user(
            email="user1@test.com",
            password="testpass123",
            name="김철수",
            nickname="김철수",
            birthday=date(1990, 1, 1),
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com",
            password="testpass123",
            name="이영희",
            nickname="이영희",
            birthday=date(1990, 1, 1),
        )

        self.category = PostCategory.objects.create(name="자유게시판")

        self.post1 = Post.objects.create(
            author=self.user1,
            title="파이썬 Django 튜토리얼",
            content="Django 프레임워크를 배우는 방법",
            category=self.category,
        )
        self.post2 = Post.objects.create(
            author=self.user2,
            title="자바스크립트 기초",
            content="React와 Django를 함께 사용하기",
            category=self.category,
        )
        self.post3 = Post.objects.create(
            author=self.user1,
            title="데이터베이스 설계",
            content="PostgreSQL 최적화 방법",
            category=self.category,
        )

        self.list_url = reverse("post-list-create")

    def test_search_by_author_name(self) -> None:
        """작성자 이름으로 검색"""
        response = self.client.get(
            self.list_url,
            {"search_filter": "author", "search": "김철수"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 2)

        for post in results:
            self.assertEqual(post["author"]["nickname"], "김철수")

    def test_search_by_title_only(self) -> None:
        """제목으로만 검색"""
        response = self.client.get(
            self.list_url,
            {"search_filter": "title", "search": "Django"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)  # 제목에 'Django'가 있는 게시글 1개
        self.assertIn("Django", results[0]["title"])

    def test_search_by_content_only(self) -> None:
        """내용으로만 검색"""
        response = self.client.get(
            self.list_url,
            {"search_filter": "content", "search": "Django"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 2)  # 내용에 'Django'가 있는 게시글 2개

    def test_search_by_title_or_content(self) -> None:
        """제목 또는 내용으로 검색"""
        response = self.client.get(
            self.list_url,
            {"search_filter": "title_or_content", "search": "Django"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 2)  # 제목 또는 내용에 'Django'가 있는 게시글 2개

    def test_search_without_filter_searches_all(self) -> None:
        """필터 없이 검색 - 제목, 내용, 작성자 모두에서 검색"""
        response = self.client.get(
            self.list_url,
            {"search": "Django"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 2)  # 어디든 'Django'가 포함된 게시글

    def test_search_with_empty_string(self) -> None:
        """빈 문자열로 검색 - 모든 게시글 반환"""
        response = self.client.get(
            self.list_url,
            {"search": ""}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 3)  # 모든 게시글 반환

    def test_search_no_results(self) -> None:
        """검색 결과가 없는 경우"""
        response = self.client.get(
            self.list_url,
            {"search_filter": "title", "search": "존재하지않는검색어"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 0)  # 결과 없음

    def test_search_case_insensitive(self) -> None:
        """대소문자 구분 없이 검색 """
        response = self.client.get(
            self.list_url,
            {"search_filter": "title", "search": "django"}  # 소문자로 검색
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)  # 대소문자 구분 없이 검색됨

    def test_search_partial_match(self) -> None:
        """부분 일치 검색 - '파이'로 검색하면 '파이썬'을 찾음"""
        response = self.client.get(
            self.list_url,
            {"search_filter": "title", "search": "파이"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertIn("파이썬", results[0]["title"])

    def test_search_with_category_filter(self) -> None:
        """검색과 카테고리 필터 동시 사용"""
        response = self.client.get(
            self.list_url,
            {
                "search": "Django",
                "category_id": str(self.category.id),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        self.assertEqual(len(results), 2)
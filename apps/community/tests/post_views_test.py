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
    # 테스트 클래스 전체에서 사용할 공통 테스트 데이터를 생성
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

    # 각 테스트 메서드 실행 전에 APIClient와 URL을 초기화
    def setUp(self) -> None:
        self.client = APIClient()
        self.list_url = reverse("post-list-create")

    # ====================
    # helpers
    # ====================

    # 테스트용 사용자를 인증 상태로 만드는 헬퍼 메서드
    def authenticate(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    # 테스트용 게시글을 생성하는 헬퍼 메서드
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
        """게시글 목록 조회가 성공 동작하는지 테스트"""
        self.create_post(author=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_post_list_search(self) -> None:
        """검색 기능이 정상 동작하는지 테스트"""
        self.create_post(author=self.user, title="Django 튜토리얼")
        self.create_post(author=self.user, title="Python 기초")
        response = self.client.get(self.list_url, {"search": "Django"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("Django", response.data[0]["title"])

    def test_post_list_filter_by_category(self) -> None:
        """카테고리 필터링이 정상 동작"""
        self.create_post(author=self.user, category=self.category)
        self.create_post(author=self.user, category=self.category2)
        response = self.client.get(self.list_url, {"category_id": str(self.category.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_post_list_invalid_category_id(self) -> None:
        """category_id가 정수가 아닐 때 400 에러를 반환 테스트"""
        response = self.client.get(self.list_url, {"category_id": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category_id는 정수여야 합니다", str(response.data))

    def test_post_list_invalid_sort_field(self) -> None:
        """허용되지 않은 정렬 필드를 사용할 때 400 에러를 반환테스트"""
        response = self.client.get(self.list_url, {"sort": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("정렬 기준이 올바르지 않습니다", str(response.data))

    def test_post_list_sort_order_asc(self) -> None:
        """오름차순 정렬이 정상 동작하는지 테스트"""
        self.create_post(author=self.user, title="C제목")
        self.create_post(author=self.user, title="A제목")
        self.create_post(author=self.user, title="B제목")
        response = self.client.get(self.list_url, {"sort": "title", "order": "asc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["title"], "A제목")

    def test_post_list_sort_order_desc(self) -> None:
        """내림차순 정렬이 정상동작하는지 테스트"""
        self.create_post(author=self.user, title="A제목")
        self.create_post(author=self.user, title="B제목")
        self.create_post(author=self.user, title="C제목")
        response = self.client.get(self.list_url, {"sort": "title", "order": "desc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["title"], "C제목")

    # ====================
    # POST /posts - 생성
    # ====================

    def test_post_create_success(self) -> None:
        """게시글 생성이 성공 동작 테스트"""
        self.authenticate(self.user)
        response = self.client.post(
            self.list_url, {"title": "새 게시글", "content": "새 내용", "category_id": self.category.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertIn("detail", response.data)
        self.assertIn("data", response.data)

    def test_post_create_unauthenticated(self) -> None:
        """인증되지 않은 사용자가 게시글을 생성하려 할 때 401 에러를 반환"""
        response = self.client.post(
            self.list_url, {"title": "제목", "content": "내용", "category_id": self.category.id}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_validation_error(self) -> None:
        """validation 실패 시 400 에러를 반환"""
        self.authenticate(self.user)
        response = self.client.post(self.list_url, {"title": "", "content": "내용", "category_id": self.category.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ====================
    # GET /posts/{id} - 상세 조회
    # ====================

    def test_post_detail_success(self) -> None:
        """게시글 상세 조회가 성공 동작하는지 테스트"""
        post = self.create_post(author=self.user)
        response = self.client.get(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], post.id)
        self.assertEqual(response.data["title"], "제목")

    def test_post_detail_invalid_id(self) -> None:
        """유효하지 않은 ID 형식으로 상세 조회 시도 시 400 에러를 반환하는지 테스트"""
        response = self.client.get(reverse("post-detail", args=["invalid"]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("잘못된 게시글 ID입니다", str(response.data))

    def test_post_detail_not_found(self) -> None:
        """존재하지 않는 게시글 ID로 상세 조회 시도 시 404 에러를 반환하는지 테스트"""
        response = self.client.get(reverse("post-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ====================
    # PUT /posts/{id} - 수정
    # ====================

    def test_post_update_success(self) -> None:
        """게시글 수정이 성공 동작하는지 테스트"""
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"title": "수정된 제목", "content": "수정된 내용", "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, "수정된 제목")

    def test_post_update_forbidden(self) -> None:
        """작성자가 아닌 사용자가 게시글을 수정하려 할 때 403 에러를 반환하는지 테스트"""
        post = self.create_post(author=self.user)
        self.authenticate(self.other_user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"title": "수정 시도", "content": "수정 시도", "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("수정 권한이 없습니다", str(response.data))

    def test_post_update_invalid_id(self) -> None:
        """유효하지 않은 ID 형식으로 수정 시도 시 400 에러를 반환하는지 테스트"""
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=["invalid"]),
            {"title": "수정", "content": "수정", "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("잘못된 게시글 ID입니다", str(response.data))

    def test_post_update_validation_error(self) -> None:
        """수정 시 validation 실패 시 400 에러를 반환하는지 테스트"""
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"title": "", "content": "내용", "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ====================
    # DELETE /posts/{id} - 삭제
    # ====================

    def test_post_delete_success(self) -> None:
        """게시글 삭제가 성공 동작하는지 테스트"""
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.delete(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

    def test_post_delete_forbidden(self) -> None:
        """작성자가 아닌 사용자가 게시글을 삭제하려 할 때 403 에러를 반환하는지 테스트"""
        post = self.create_post(author=self.user)
        self.authenticate(self.other_user)
        response = self.client.delete(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("삭제 권한이 없습니다", str(response.data))
        self.assertEqual(Post.objects.count(), 1)

    def test_post_delete_invalid_id(self) -> None:
        """유효하지 않은 ID 형식으로 삭제 시도 시 400 에러를 반환하는지 테스트"""
        self.authenticate(self.user)
        response = self.client.delete(reverse("post-detail", args=["invalid"]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("잘못된 게시글 ID입니다", str(response.data))

    def test_post_delete_unauthenticated(self) -> None:
        """인증되지 않은 사용자가 게시글을 삭제하려 할 때 401 에러를 반환하는지 테스트"""
        post = self.create_post(author=self.user)
        response = self.client.delete(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

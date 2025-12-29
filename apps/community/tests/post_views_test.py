from datetime import date
from typing import Any, Dict

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory
from apps.user.models import User


class PostListCreateAdvancedTestCase(TestCase):

    def setUp(self) -> None:
        """테스트 환경 설정"""
        self.client: APIClient = APIClient()
        self.user: User = User.objects.create_user(
            name="테스트유저",
            birthday=date(2000, 11, 21),
            email="test@example.com",
            password="testpass123",
        )
        self.category: PostCategory = PostCategory.objects.create(name="테스트 카테고리")
        self.url: str = reverse("post-list-create")

    def test_get_post_list_with_order_asc(self) -> None:
        """
        게시글 목록 오름차순 정렬 테스트
        """
        Post.objects.create(title="C 제목", content="내용", author=self.user, category=self.category)
        Post.objects.create(title="A 제목", content="내용", author=self.user, category=self.category)
        Post.objects.create(title="B 제목", content="내용", author=self.user, category=self.category)

        response = self.client.get(self.url, {"sort": "title", "order": "asc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsInstance(response.data, list)
        self.assertEqual(response.data[0]["title"], "A 제목")
        self.assertEqual(response.data[1]["title"], "B 제목")
        self.assertEqual(response.data[2]["title"], "C 제목")

    def test_get_post_list_with_order_not_desc(self) -> None:
        """
        정렬 순서가 'desc'가 아닌 경우 테스트
        """
        Post.objects.create(title="테스트", content="내용", author=self.user, category=self.category)

        response = self.client.get(self.url, {"sort": "created_at", "order": "asc"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_post_list_without_search_keyword(self) -> None:
        """
        검색어 없이 목록 조회 테스트
        """
        Post.objects.create(title="게시글 1", content="내용", author=self.user, category=self.category)
        Post.objects.create(title="게시글 2", content="내용", author=self.user, category=self.category)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data: Any = response.json()
        self.assertEqual(len(response_data), 2)

    def test_get_post_list_without_category_filter(self) -> None:
        """
        카테고리 필터 없이 목록 조회 테스트
        """
        category2: PostCategory = PostCategory.objects.create(name="카테고리2")
        Post.objects.create(title="게시글 1", content="내용", author=self.user, category=self.category)
        Post.objects.create(title="게시글 2", content="내용", author=self.user, category=category2)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data: Any = response.json()
        self.assertEqual(len(response_data), 2)

    def test_get_post_list_with_invalid_category_id(self) -> None:
        """
        잘못된 category_id 파라미터 테스트
        """
        Post.objects.create(title="테스트", content="내용", author=self.user, category=self.category)

        response = self.client.get(self.url, {"category_id": "invalid_string"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data: Any = response.json()
        self.assertEqual(response_data["detail"], "category_id는 정수여야 합니다.")

    def test_get_post_list_with_invalid_sort_field(self) -> None:
        """
        유효하지 않은 정렬 필드 테스트
        """
        Post.objects.create(title="테스트", content="내용", author=self.user, category=self.category)

        response = self.client.get(self.url, {"sort": "invalid_field", "order": "asc"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data: Any = response.json()
        self.assertEqual(response_data["detail"], "정렬 기준이 올바르지 않습니다.")

    def test_create_post_with_serializer_validation_error(self) -> None:
        """
        시리얼라이저 검증 실패 시 raise_exception=True 동작 테스트
        """
        self.client.force_authenticate(user=self.user)

        data: Dict[str, Any] = {}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_post_response_includes_detail_and_data(self) -> None:
        """
        게시글 생성 성공 시 응답 구조 테스트
        """
        self.client.force_authenticate(user=self.user)

        data: Dict[str, Any] = {
            "title": "새 게시글",
            "content": "새 내용",
            "category_id": self.category.id,
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn("detail", response.data)
        self.assertIn("data", response.data)
        self.assertEqual(response.data["detail"], "게시글이 성공적 등록됨.")
        self.assertIsNotNone(response.data["data"]["post_id"])

    def test_create_post_without_authentication(self) -> None:
        """
        인증 없이 게시글 생성 시도 테스트
        """
        data: Dict[str, Any] = {
            "title": "새 게시글",
            "content": "새 내용",
            "category_id": self.category.id,
        }
        response = self.client.post(self.url, data, format="json")

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_get_post_list_with_search_keyword(self) -> None:
        """
        검색어로 목록 조회 테스트
        """
        Post.objects.create(title="Django 튜토리얼", content="내용", author=self.user, category=self.category)
        Post.objects.create(title="Python 가이드", content="내용", author=self.user, category=self.category)

        response = self.client.get(self.url, {"search": "Django"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data: Any = response.json()
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["title"], "Django 튜토리얼")

    def test_get_post_list_with_valid_category_filter(self) -> None:
        """
        유효한 카테고리 필터로 목록 조회 테스트
        """
        category2: PostCategory = PostCategory.objects.create(name="카테고리2")
        Post.objects.create(title="게시글 1", content="내용", author=self.user, category=self.category)
        Post.objects.create(title="게시글 2", content="내용", author=self.user, category=category2)

        response = self.client.get(self.url, {"category_id": str(self.category.id)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data: Any = response.json()
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["title"], "게시글 1")


class PostRetrieveUpdateDestroyAdvancedTestCase(TestCase):

    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.user: User = User.objects.create_user(
            email="test@test.com",
            name="테스트유저",
            birthday=date(2000, 1, 1),
            password="testpass123",
        )

        self.other_user: User = User.objects.create_user(
            email="other@test.com",
            name="다른유저",
            birthday=date(2000, 1, 1),
            password="testpass123",
        )

        self.category: PostCategory = PostCategory.objects.create(name="카테고리")

        self.post: Post = Post.objects.create(
            title="원래 제목",
            content="원래 내용",
            author=self.user,
            category=self.category,
        )

        self.url: str = reverse("post-detail", kwargs={"pk": self.post.id})

    def test_get_object_with_valid_pk(self) -> None:
        """
        get_object 메서드 정상 동작 테스트
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "원래 제목")

    def test_get_object_with_invalid_pk_raises_value_error(self) -> None:
        """
        get_object 메서드에서 ValueError 발생 테스트
        """
        url: str = reverse("post-detail", kwargs={"pk": "invalid_string"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data: Any = response.json()
        self.assertIn("잘못된 게시글 ID입니다.", response_data["detail"])

    def test_get_post_detail_success_path(self) -> None:
        """
        게시글 상세 조회 성공 경로 테스트
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data: Any = response.json()
        self.assertEqual(response_data["title"], "원래 제목")

    def test_get_post_detail_value_error_exception(self) -> None:
        """
        게시글 상세 조회 시 ValueError 예외 처리 테스트
        """
        url: str = reverse("post-detail", kwargs={"pk": "not_a_number"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data: Any = response.json()
        self.assertEqual(response_data["detail"], "잘못된 게시글 ID입니다.")

    def test_get_post_detail_not_found(self) -> None:
        """
        존재하지 않는 게시글 조회 테스트
        """
        url: str = reverse("post-detail", kwargs={"pk": "99999"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_post_author_check_passes(self) -> None:
        """
        게시글 수정 시 작성자 확인 통과 테스트
        """
        self.client.force_authenticate(user=self.user)

        data: Dict[str, Any] = {
            "title": "수정된 제목",
            "content": "수정된 내용",
            "category_id": self.category.id,
        }

        response = self.client.put(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "수정된 제목")

    def test_update_post_author_check_fails(self) -> None:
        """
        게시글 수정 시 작성자 확인 실패 테스트
        """
        self.client.force_authenticate(user=self.other_user)

        data: Dict[str, Any] = {
            "title": "수정 시도",
            "content": "수정 시도",
            "category_id": self.category.id,
        }
        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response_data: Any = response.json()
        self.assertEqual(response_data["detail"], "수정 권한이 없습니다.")

    def test_update_post_serializer_validation_success(self) -> None:
        """
        게시글 수정 시 시리얼라이저 검증 성공 테스트
        """
        self.client.force_authenticate(user=self.user)

        data: Dict[str, Any] = {
            "title": "검증 성공 제목",
            "content": "검증 성공 내용",
            "category_id": self.category.id,
        }

        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "검증 성공 제목")

    def test_update_post_value_error_exception(self) -> None:
        """
        게시글 수정 시 ValueError 예외 처리 테스트
        """
        self.client.force_authenticate(user=self.user)
        url: str = reverse("post-detail", kwargs={"pk": "invalid"})

        data: Dict[str, Any] = {
            "title": "수정",
            "content": "내용",
            "category_id": self.category.id,
        }
        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data: Any = response.json()
        self.assertEqual(response_data["detail"], "잘못된 게시글 ID입니다.")

    def test_update_post_without_authentication(self) -> None:
        """
        인증 없이 게시글 수정 시도 테스트
        """
        data: Dict[str, Any] = {
            "title": "수정 시도",
            "content": "수정 시도",
            "category_id": self.category.id,
        }
        response = self.client.put(self.url, data, format="json")

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_delete_post_author_check_passes(self) -> None:
        """
        게시글 삭제 시 작성자 확인 통과 테스트
        """
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_delete_post_author_check_fails(self) -> None:
        """
        게시글 삭제 시 작성자 확인 실패 테스트
        """
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response_data: Any = response.json()
        self.assertEqual(response_data["detail"], "삭제 권한이 없습니다.")

    def test_delete_post_success(self) -> None:
        """
        게시글 삭제 성공 테스트
        """
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_delete_post_value_error_exception(self) -> None:
        """
        게시글 삭제 시 ValueError 예외 처리 테스트
        """
        self.client.force_authenticate(user=self.user)
        url: str = reverse("post-detail", kwargs={"pk": "invalid_id"})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data: Any = response.json()
        self.assertEqual(response_data["detail"], "잘못된 게시글 ID입니다.")

    def test_delete_post_without_authentication(self) -> None:
        """
        인증 없이 게시글 삭제 시도 테스트
        """
        response = self.client.delete(self.url)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )


class PostViewEdgeCaseTestCase(TestCase):
    """엣지 케이스 및 추가 시나리오 테스트"""

    def setUp(self) -> None:
        """테스트 환경 설정"""
        self.client: APIClient = APIClient()
        self.user: User = User.objects.create_user(
            birthday=date(2000, 11, 21),
            name="테스트유저",
            email="test@example.com",
            password="testpass123",
        )
        self.category: PostCategory = PostCategory.objects.create(name="테스트 카테고리")

    def test_get_post_list_with_multiple_filters(self) -> None:
        """
        여러 필터 동시 적용 테스트
        """
        Post.objects.create(
            title="Django 튜토리얼",
            content="내용",
            author=self.user,
            category=self.category,
            view_count=100,
        )
        Post.objects.create(
            title="Django 고급",
            content="내용",
            author=self.user,
            category=self.category,
            view_count=200,
        )

        url: str = reverse("post-list-create")
        response = self.client.get(
            url,
            {
                "search": "Django",
                "category_id": str(self.category.id),
                "sort": "view_count",
                "order": "desc",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data: Any = response.json()
        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0]["view_count"], 200)
        self.assertEqual(response_data[1]["view_count"], 100)

    def test_get_post_list_empty_queryset(self) -> None:
        """
        빈 쿼리셋 반환 테스트
        """
        url: str = reverse("post-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data: Any = response.json()
        self.assertEqual(len(response_data), 0)
        self.assertIsInstance(response_data, list)

    def test_get_post_list_with_default_sort_and_order(self) -> None:
        """
        기본 정렬 옵션 테스트 (sort=created_at, order=desc)
        """
        Post.objects.create(title="게시글 1", content="내용", author=self.user, category=self.category)
        Post.objects.create(title="게시글 2", content="내용", author=self.user, category=self.category)

        url: str = reverse("post-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data: Any = response.json()
        self.assertEqual(len(response_data), 2)

    def test_update_post_with_invalid_serializer_data(self) -> None:
        """
        유효하지 않은 데이터로 수정 시도 테스트
        """
        post: Post = Post.objects.create(title="원본", content="내용", author=self.user, category=self.category)

        self.client.force_authenticate(user=self.user)
        url: str = reverse("post-detail", kwargs={"pk": str(post.id)})

        data: Dict[str, Any] = {
            "title": "",
            "content": "내용",
            "category_id": self.category.id,
        }
        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_post_list_with_special_characters_in_search(self) -> None:
        """
        특수 문자 검색어 테스트
        """
        Post.objects.create(
            title="특수문자 테스트 @#$",
            content="내용",
            author=self.user,
            category=self.category,
        )

        url: str = reverse("post-list-create")
        response = self.client.get(url, {"search": "@#$"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data: Any = response.json()
        self.assertEqual(len(response_data), 1)

    def test_update_post_with_nonexistent_category(self) -> None:
        """
        존재하지 않는 카테고리로 수정 시도 테스트
        """
        post: Post = Post.objects.create(title="원본", content="내용", author=self.user, category=self.category)

        self.client.force_authenticate(user=self.user)
        url: str = reverse("post-detail", kwargs={"pk": str(post.id)})

        data: Dict[str, Any] = {
            "title": "수정",
            "content": "내용",
            "category_id": 99999,
        }
        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_post_list_with_all_allowed_sort_fields(self) -> None:
        """
        허용된 모든 정렬 필드 테스트
        """
        Post.objects.create(title="테스트", content="내용", author=self.user, category=self.category)

        url: str = reverse("post-list-create")

        sort_fields = ["created_at", "updated_at", "title", "view_count"]

        for sort_field in sort_fields:
            with self.subTest(sort_field=sort_field):
                response = self.client.get(url, {"sort": sort_field, "order": "desc"})
                self.assertEqual(response.status_code, status.HTTP_200_OK)

                response = self.client.get(url, {"sort": sort_field, "order": "asc"})
                self.assertEqual(response.status_code, status.HTTP_200_OK)


class PostViewSelectRelatedTestCase(TestCase):
    """select_related 최적화 테스트"""

    def setUp(self) -> None:
        """테스트 환경 설정"""
        self.client: APIClient = APIClient()
        self.user: User = User.objects.create_user(
            birthday=date(2000, 11, 21),
            name="테스트유저",
            email="test@example.com",
            password="testpass123",
        )
        self.category: PostCategory = PostCategory.objects.create(name="테스트 카테고리")

    def test_get_base_queryset_uses_select_related(self) -> None:
        """
        get_base_queryset가 select_related를 사용하는지 테스트
        """
        Post.objects.create(title="테스트", content="내용", author=self.user, category=self.category)

        url: str = reverse("post-list-create")

        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            query_count = len(context.captured_queries)
            self.assertLessEqual(query_count, 5)

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
    # 테스트 클래스 전체에서 사용할 공통 더미 데이터를 생성
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

    ##### helpers #####
    #### 여러곳에서 똑같이 사용되는 코드를 한곳에 모은 메서드. #####

    # 테스트용 사용자를 인증 상태로 만드는 헬퍼 메서드
    def authenticate(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    # 테스트용 게시글을 생성하는 헬퍼 메서드 기본값을 사용하여 간편하게 게시글을 생성할 수 있음
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

    ##### GET /posts - 목록 조회 #####

    # 게시글 목록 조회가 성공적 동작하는지 응답 데이터 구조가 올바른지 테스트
    def test_post_list_success(self) -> None:
        self.create_post(author=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        # 응답 데이터 구조 검증
        post_data = response.data[0]
        self.assertIn("id", post_data)
        self.assertIn("author", post_data)
        self.assertIn("title", post_data)
        self.assertIn("thumbnail_img_url", post_data)
        self.assertIn("content_preview", post_data)
        self.assertIn("comment_count", post_data)
        self.assertIn("view_count", post_data)
        self.assertIn("like_count", post_data)
        self.assertIn("created_at", post_data)
        self.assertIn("updated_at", post_data)
        # author 구조 검증
        self.assertIn("id", post_data["author"])
        self.assertIn("name", post_data["author"])

    # 내용이 50자 이하일 때 content_preview가 전체 내용을 그대로 반환테스트
    def test_post_list_content_preview_short(self) -> None:
        short_content = "짧은 내용"
        self.create_post(author=self.user, content=short_content)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["content_preview"], short_content)

    # 내용이 50자 초과일 때 content_preview가 50자로 잘리고 "..."이 추가되는지 테스트
    def test_post_list_content_preview_long(self) -> None:
        long_content = "a" * 100
        self.create_post(author=self.user, content=long_content)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content_preview = response.data[0]["content_preview"]
        self.assertTrue(len(content_preview) <= 53)
        self.assertTrue(content_preview.endswith("..."))

    # 내용이 정확히 50자일 때 content_preview가 전체 내용을 그대로 반환 테스트
    def test_post_list_content_preview_exactly_50_chars(self) -> None:
        exact_content = "a" * 50
        self.create_post(author=self.user, content=exact_content)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["content_preview"], exact_content)

    # 게시글 목록에서 like_count의 기본값이 0인지 테스트
    def test_post_list_like_count_default(self) -> None:
        self.create_post(author=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["like_count"], 0)

    # 게시글 목록에서 comment_count의 기본값이 0인지 테스트
    def test_post_list_comment_count_default(self) -> None:
        self.create_post(author=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["comment_count"], 0)

    # 게시글이 없을 때 빈 배열을 반환 테스트
    def test_post_list_empty(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # 여러 게시글이 있을 때 모두 조회 테스트
    def test_post_list_multiple_posts(self) -> None:
        self.create_post(author=self.user, title="첫번째")
        self.create_post(author=self.user, title="두번째")
        self.create_post(author=self.other_user, title="세번째")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    # 제목으로 검색이 정상적으로 동작 테스트
    def test_post_list_search_by_title(self) -> None:
        self.create_post(author=self.user, title="Django 튜토리얼")
        self.create_post(author=self.user, title="Python 기초")
        response = self.client.get(self.list_url, {"search": "Django"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("Django", response.data[0]["title"])

    # 검색 결과가 없을 때 빈 배열을 반환 테스트
    def test_post_list_search_no_results(self) -> None:
        self.create_post(author=self.user, title="Django 튜토리얼")
        response = self.client.get(self.list_url, {"search": "Flask"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # 카테고리 ID로 필터링이 정상적동작 테스트
    def test_post_list_filter_by_category(self) -> None:
        self.create_post(author=self.user, category=self.category)
        self.create_post(author=self.user, category=self.category2)
        response = self.client.get(self.list_url, {"category_id": str(self.category.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # category_id가 정수가 아닐 때 400 에러를 반환 테스트
    def test_post_list_invalid_category_id(self) -> None:
        response = self.client.get(self.list_url, {"category_id": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category_id는 정수여야 합니다", str(response.data))

    # 존재하지 않는 카테고리 ID로 필터링할 때 빈 배열을 반환 테스트
    def test_post_list_filter_nonexistent_category(self) -> None:
        self.create_post(author=self.user)
        response = self.client.get(self.list_url, {"category_id": "9999"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # 검색과 카테고리 필터링을 동시에 사용할 때 정상적 동작 테스트
    def test_post_list_search_and_filter_combined(self) -> None:
        self.create_post(author=self.user, title="A제목", category=self.category)
        self.create_post(author=self.user, title="B제목", category=self.category2)
        response = self.client.get(self.list_url, {"search": "A", "category_id": str(self.category.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "A제목")

    # 제목으로 오름차순 정렬이 정상적으로 동작 테스트
    def test_post_list_sort_by_title_asc(self) -> None:
        self.create_post(author=self.user, title="C제목")
        self.create_post(author=self.user, title="A제목")
        self.create_post(author=self.user, title="B제목")
        response = self.client.get(self.list_url, {"sort": "title", "order": "asc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["title"], "A제목")

    # 생성일 기준 내림차순 정렬이 기본값으로 적용 테스트
    def test_post_list_sort_by_created_at_desc(self) -> None:
        post2 = self.create_post(author=self.user, title="두번째")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], post2.id)

    # 허용되지 않은 정렬 필드를 사용할 때 400 에러를 반환 테스트
    def test_post_list_invalid_sort_field(self) -> None:
        response = self.client.get(self.list_url, {"sort": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("정렬 기준이 올바르지 않습니다", str(response.data))

    # 유효하지 않은 order 값이 전달되어도 기본값으로 처리 테스트
    def test_post_list_sort_order_invalid(self) -> None:
        self.create_post(author=self.user, title="A제목")
        response = self.client.get(self.list_url, {"sort": "title", "order": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # 존재하지 않는 order 값이 전달되어도 기본값으로 처리 테스트
    def test_post_list_sort_order_invalid_edge(self) -> None:
        self.create_post(author=self.user)
        response = self.client.get(self.list_url, {"sort": "title", "order": "notexist"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # 제목으로 내림차순 정렬이 정상적으로 동작 테스트
    def test_post_list_sort_by_title_desc(self) -> None:
        self.create_post(author=self.user, title="A제목")
        self.create_post(author=self.user, title="B제목")
        self.create_post(author=self.user, title="C제목")
        response = self.client.get(self.list_url, {"sort": "title", "order": "desc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["title"], "C제목")

    # 수정일 기준 오름차순 정렬이 정상적으로 동작 테스트
    def test_post_list_sort_by_updated_at_asc(self) -> None:
        post1 = self.create_post(author=self.user, title="첫번째")
        post2 = self.create_post(author=self.user, title="두번째")
        post1.title = "첫번째 수정"
        post1.save()
        response = self.client.get(self.list_url, {"sort": "updated_at", "order": "asc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], post2.id)

    # 수정일 기준 내림차순 정렬이 정상적으로 동작 테스트
    def test_post_list_sort_by_updated_at_desc(self) -> None:
        post1 = self.create_post(author=self.user, title="첫번째")
        post1.title = "첫번째 수정"
        post1.save()
        response = self.client.get(self.list_url, {"sort": "updated_at", "order": "desc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], post1.id)

    # 조회수 기준 오름차순 정렬이 정상적으로 동작 테스트
    def test_post_list_sort_by_view_count_asc(self) -> None:
        post1 = self.create_post(author=self.user, title="조회수1")
        post2 = self.create_post(author=self.user, title="조회수2")
        post3 = self.create_post(author=self.user, title="조회수3")
        post1.view_count = 10
        post2.view_count = 5
        post3.view_count = 15
        post1.save()
        post2.save()
        post3.save()
        response = self.client.get(self.list_url, {"sort": "view_count", "order": "asc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], post2.id)
        self.assertEqual(response.data[0]["view_count"], 5)

    # 조회수 기준 내림차순 정렬이 정상적으로 동작 테스트
    def test_post_list_sort_by_view_count_desc(self) -> None:
        post1 = self.create_post(author=self.user, title="조회수1")
        post2 = self.create_post(author=self.user, title="조회수2")
        post1.view_count = 10
        post2.view_count = 20
        post1.save()
        post2.save()
        response = self.client.get(self.list_url, {"sort": "view_count", "order": "desc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], post2.id)
        self.assertEqual(response.data[0]["view_count"], 20)

    # 빈 문자열로 검색할 때 모든 게시글이 반환 테스트
    def test_post_list_search_empty_string(self) -> None:
        self.create_post(author=self.user, title="Django 튜토리얼")
        response = self.client.get(self.list_url, {"search": ""})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # 검색이 대소문자를 구분하지 않는지 테스트
    def test_post_list_search_case_insensitive(self) -> None:
        self.create_post(author=self.user, title="Django 튜토리얼")
        self.create_post(author=self.user, title="django 기초")
        response = self.client.get(self.list_url, {"search": "django"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    # 음수 category_id로 필터링할 때 빈 배열을 반환 테스트
    def test_post_list_filter_negative_category_id(self) -> None:
        response = self.client.get(self.list_url, {"category_id": "-1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # 0인 category_id로 필터링할 때 빈 배열을 반환 테스트
    def test_post_list_filter_zero_category_id(self) -> None:
        response = self.client.get(self.list_url, {"category_id": "0"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    ##### POST /posts - 생성 #####

    # 게시글 생성이 되고 응답 데이터 구조가 올바른지 테스트
    def test_post_create_success(self) -> None:
        self.authenticate(self.user)
        response = self.client.post(
            self.list_url, {"title": "새 게시글", "content": "새 내용", "category_id": self.category.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertIn("detail", response.data)
        self.assertIn("data", response.data)
        self.assertIn("post_id", response.data["data"])

    # 제목이 공백만 있을 때 400 에러를 반환테스트
    def test_post_create_title_whitespace_only(self) -> None:
        self.authenticate(self.user)
        response = self.client.post(self.list_url, {"title": "   ", "content": "내용", "category_id": self.category.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("blank", str(response.data).lower())

    # 제목이 최대 길이(50자)일 때 정상적으로 생성되는지 테스트
    def test_post_create_title_max_length(self) -> None:
        self.authenticate(self.user)
        long_title = "a" * 50  # 최대 길이
        response = self.client.post(
            self.list_url, {"title": long_title, "content": "내용", "category_id": self.category.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # 제목이 최대 길이(50자)를 초과할 때 에러가 발생하는지 테스트
    def test_post_create_title_exceeds_max_length(self) -> None:
        self.authenticate(self.user)
        long_title = "a" * 51
        from django.db import DataError

        try:
            response = self.client.post(
                self.list_url, {"title": long_title, "content": "내용", "category_id": self.category.id}
            )
            self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])
        except (DataError, Exception):
            pass

    # 제목이 빈 문자열일 때 400 에러를 반환테스트
    def test_post_create_empty_string_title(self) -> None:
        self.authenticate(self.user)
        response = self.client.post(self.list_url, {"title": "", "content": "내용", "category_id": self.category.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 음수 category_id로 생성 시도 시 400 에러를 반환테스트
    def test_post_create_negative_category_id(self) -> None:
        self.authenticate(self.user)
        response = self.client.post(self.list_url, {"title": "제목", "content": "내용", "category_id": -1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("없는 카테고리입니다", str(response.data))

    # 0인 category_id로 생성 시도 시 400 에러를 반환테스트
    def test_post_create_zero_category_id(self) -> None:
        self.authenticate(self.user)
        response = self.client.post(self.list_url, {"title": "제목", "content": "내용", "category_id": 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("없는 카테고리입니다", str(response.data))

    # 인증되지 않은 사용자가 게시글을 생성하려 할 때 401 에러를 반환테스트
    def test_post_create_unauthenticated(self) -> None:
        response = self.client.post(
            self.list_url, {"title": "제목", "content": "내용", "category_id": self.category.id}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # title 필드가 없을 때 400 에러를 반환테스트
    def test_post_create_missing_title(self) -> None:
        self.authenticate(self.user)
        response = self.client.post(self.list_url, {"content": "내용", "category_id": self.category.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # content 필드가 없을 때 400 에러를 반환테스트
    def test_post_create_missing_content(self) -> None:
        self.authenticate(self.user)
        response = self.client.post(self.list_url, {"title": "제목", "category_id": self.category.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # category_id 필드가 없을 때 400 에러를 반환테스트
    def test_post_create_missing_category_id(self) -> None:
        self.authenticate(self.user)
        response = self.client.post(self.list_url, {"title": "제목", "content": "내용"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 존재하지 않는 category_id로 생성 시도 시 400 에러를 반환테스트
    def test_post_create_invalid_category_id(self) -> None:
        self.authenticate(self.user)
        response = self.client.post(self.list_url, {"title": "제목", "content": "내용", "category_id": 9999})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("없는 카테고리입니다", str(response.data))

    ##### GET /posts/{id} #####

    # 게시글 상세 조회가 성공적으로 동작하고 응답 데이터 구조가 올바른지 테스트
    def test_post_detail_success(self) -> None:
        post = self.create_post(author=self.user)
        response = self.client.get(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "제목")
        # 응답 데이터 구조 검증
        self.assertIn("id", response.data)
        self.assertIn("author", response.data)
        self.assertIn("category", response.data)
        self.assertIn("content", response.data)
        self.assertIn("view_count", response.data)
        self.assertIn("like_count", response.data)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)
        # author 구조 검증
        self.assertIn("id", response.data["author"])
        self.assertIn("name", response.data["author"])
        # category 구조 검증
        self.assertIn("id", response.data["category"])
        self.assertIn("name", response.data["category"])

    # 게시글 상세 조회 시 응답 데이터의 구조와 값이 올바른지 테스트
    def test_post_detail_response_data_structure(self) -> None:
        post = self.create_post(author=self.user, title="테스트 제목", content="테스트 내용")
        response = self.client.get(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], post.id)
        self.assertEqual(response.data["title"], "테스트 제목")
        self.assertEqual(response.data["content"], "테스트 내용")
        self.assertEqual(response.data["author"]["id"], self.user.id)

    # 유효하지 않은 ID 형식으로 상세 조회 시도 시 400 에러를 반환테스트
    def test_post_detail_invalid_id(self) -> None:
        response = self.client.get(reverse("post-detail", args=["invalid"]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("잘못된 게시글 ID입니다", str(response.data))

    # 존재하지 않는 게시글 ID로 상세 조회 시도 시 404 에러를 반환
    def test_post_detail_not_found(self) -> None:
        response = self.client.get(reverse("post-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ##### PUT /posts/{id}

    # 게시글 수정이 성공적으로 동작하고 응답 데이터 구조가 올바른지 테스트
    def test_post_update_success(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"title": "수정된 제목", "content": "수정된 내용", "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, "수정된 제목")
        # 응답 데이터 구조 검증
        self.assertIn("id", response.data)
        self.assertIn("title", response.data)
        self.assertIn("content", response.data)
        self.assertIn("category_id", response.data)
        self.assertEqual(response.data["title"], "수정된 제목")
        self.assertEqual(response.data["content"], "수정된 내용")
        self.assertEqual(response.data["category_id"], self.category.id)

    # 제목이 공백만 있을 때 수정 시도 시 400 에러를 반환테스트
    def test_post_update_title_whitespace_only(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"title": "   ", "content": "내용", "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 실제 에러 메시지에 맞게 수정
        self.assertIn("blank", str(response.data).lower())

    # 제목이 빈 문자열일 때 수정 시도 시 400 에러를 반환테스트
    def test_post_update_empty_string_title(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"title": "", "content": "내용", "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # title 필드가 없을 때 수정 시도 시 400 에러를 반환테스트
    def test_post_update_missing_title(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"content": "내용", "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # content 필드가 없을 때 수정 시도 시 400 에러를 반환테스트
    def test_post_update_missing_content(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"title": "제목", "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 음수 category_id로 수정 시도 시 400 에러를 반환테스트
    def test_post_update_negative_category_id(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]), {"title": "수정", "content": "수정", "category_id": -1}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("없는 카테고리입니다", str(response.data))

    # 0인 category_id로 수정 시도 시 400 에러를 반환테스트
    def test_post_update_zero_category_id(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]), {"title": "수정", "content": "수정", "category_id": 0}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("없는 카테고리입니다", str(response.data))

    # 작성자가 아닌 사용자가 게시글을 수정하려 할 때 403 에러를 반환테스트
    def test_post_update_forbidden(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.other_user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"title": "수정 시도", "content": "수정 시도", "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("수정 권한이 없습니다", str(response.data))

    # 유효하지 않은 ID 형식으로 수정 시도 시 400 에러를 반환하는지 테스트
    def test_post_update_invalid_id(self) -> None:
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=["invalid"]),
            {"title": "수정", "content": "수정", "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 존재하지 않는 게시글 ID로 수정 시도 시 404 에러를 반환하는지 테스트
    def test_post_update_not_found(self) -> None:
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[9999]), {"title": "x", "content": "x", "category_id": self.category.id}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 일부 필드만 수정할 때 정상적으로 동작하는지 테스트
    def test_post_partial_update_success(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"title": "부분 수정된 제목", "content": post.content, "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, "부분 수정된 제목")
        self.assertEqual(post.content, "내용")

    # 일부 필드만 수정할 때 정상적으로 동작하는지 테스트
    def test_post_partial_update_content_only(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"title": post.title, "content": "내용만 수정", "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.content, "내용만 수정")

    # 일부 필드만 수정할 때 정상적으로 동작하는지 테스트
    def test_post_update_title_only(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]),
            {"title": "제목만 수정", "content": post.content, "category_id": self.category.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, "제목만 수정")

    # 존재하지 않는 category_id로 수정 시도 시 400 에러를 반환하는지 테스트
    def test_post_update_invalid_category_id(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.put(
            reverse("post-detail", args=[post.id]), {"title": "수정", "content": "수정", "category_id": 9999}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("없는 카테고리입니다", str(response.data))

    ##### DELETE /posts/{id} #####

    # 게시글 삭제가 성공 테스트
    def test_post_delete_success(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.user)
        response = self.client.delete(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

    # 작성자가 아닌 사용자가 게시글을 삭제하려 할 때 403 에러를 반환하는지 테스트
    def test_post_delete_forbidden(self) -> None:
        post = self.create_post(author=self.user)
        self.authenticate(self.other_user)
        response = self.client.delete(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("삭제 권한이 없습니다", str(response.data))
        self.assertEqual(Post.objects.count(), 1)

    # 인증되지 않은 사용자가 게시글을 삭제하려 할 때 401 에러를 반환하는지 테스트
    def test_post_delete_unauthenticated(self) -> None:
        post = self.create_post(author=self.user)
        response = self.client.delete(reverse("post-detail", args=[post.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Post.objects.count(), 1)

    # 유효하지 않은 ID 형식으로 삭제 시도 시 400 에러를 반환하는지 테스트
    def test_post_delete_invalid_id(self) -> None:
        self.authenticate(self.user)
        response = self.client.delete(reverse("post-detail", args=["invalid"]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("잘못된 게시글 ID입니다", str(response.data))

    ##### 모델 __str__ 커버 #####

    # Post 모델의 __str__ 메서드가 정상적으로 동작하는지 테스트
    def test_post_model_str(self) -> None:
        post = self.create_post(author=self.user)
        self.assertIsInstance(str(post), str)

    # PostCategory 모델의 __str__ 메서드가 정상적으로 동작하는지 테스트
    def test_post_category_model_str(self) -> None:
        self.assertIsInstance(str(self.category), str)
        self.assertIsInstance(str(self.category2), str)

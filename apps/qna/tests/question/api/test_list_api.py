from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.exceptions.exception_messages import EMS
from apps.qna.models import Question, QuestionCategory
from apps.user.models import User
from apps.user.models.user import RoleChoices


class QuestionListAPITests(APITestCase):

    # 질문이 없을 때 (빈 리스트)
    def setUp(self) -> None:
        self.url = reverse("questions")

    def test_empty_question_list_returns_empty_results(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    # 질문 목록 정상 조회
    def test_question_list_success(self) -> None:
        user = User.objects.create_user(
            email="test@test.com",
            password="test1234",
            name="테스트 유저",
            role=RoleChoices.ST,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
        )

        category = QuestionCategory.objects.create(name="Backend")

        Question.objects.create(
            author=user,
            category=category,
            title="질문 제목",
            content="질문 내용",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

        item = response.data["results"][0]
        self.assertEqual(item["title"], "질문 제목")

    # 필터 결과가 없을 때도 정상
    def test_filter_returns_empty_results(self) -> None:
        response = self.client.get(self.url, {"search_keyword": "없는검색어"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    # page가 커도 정상 (빈 리스트)
    def test_large_page_returns_empty_results(self) -> None:
        response = self.client.get(self.url, {"page": 9999})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    # page가 0이면 400
    def test_invalid_page_zero_returns_400(self) -> None:
        response = self.client.get(self.url, {"page": 0})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # page가 문자열이면 400
    def test_invalid_page_string_returns_400(self) -> None:
        response = self.client.get(self.url, {"page": "abc"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # content_preview에서 HTML 태그가 제거되었는지 확인하는 테스트
    def test_question_list_content_preview_strips_tags(self) -> None:
        # 1. 테스트 데이터 생성 (User, Category)
        user = User.objects.create_user(
            email="strip@test.com",
            password="test1234",
            name="태그제거테스트",
            role=RoleChoices.ST,
            phone_number="010-1111-2222",
            gender="M",
            birthday="2000-01-01",
        )
        category = QuestionCategory.objects.create(name="Frontend")

        # 2. HTML 태그가 포함된 질문 생성
        html_content = "<p>이것은 <b>굵은</b> 글씨이고, <br>줄바꿈도 있습니다.</p>"
        Question.objects.create(
            author=user,
            category=category,
            title="HTML 태그 포함 질문",
            content=html_content,
        )

        # 3. API 호출
        response = self.client.get(self.url)

        # 4. 검증
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data["results"][0]

        # 태그가 제거된 순수 텍스트만 남아있는지 확인
        expected_text = "이것은 굵은 글씨이고, 줄바꿈도 있습니다."

        # strip_tags 결과에 따라 공백 처리가 조금 다를 수 있으므로 핵심 단어 포함 여부나 태그 부재 여부로 검증
        self.assertNotIn("<p>", item["content_preview"])
        self.assertNotIn("<b>", item["content_preview"])
        self.assertNotIn("<br>", item["content_preview"])
        self.assertIn("이것은 굵은 글씨이고", item["content_preview"])

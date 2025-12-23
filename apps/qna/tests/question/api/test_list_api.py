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

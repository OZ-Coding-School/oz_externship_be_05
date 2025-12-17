from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.qna.models import Question, QuestionCategory
from apps.user.models import User
from apps.user.models.user import RoleChoices


class QuestionListAPITests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="apitest@test.com",
            password="test1234",
            name="유저",
            role=RoleChoices.ST,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
        )

        self.category = QuestionCategory.objects.create(name="백엔드")

        self.url = reverse("questions")

    # 질문 없을 때 404
    def test_empty_question_list(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["error_detail"],
            "조회 가능한 질문이 존재하지 않습니다.",
        )

    # 목록 조회 성공
    def test_question_list_success(self) -> None:
        Question.objects.create(
            author=self.user,
            title="질문 제목",
            content="내용",
            category=self.category,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    # answered=true 필터
    def test_answered_filter_true(self) -> None:
        question = Question.objects.create(
            author=self.user,
            title="답변 질문",
            content="내용",
            category=self.category,
        )

        question.answers.create(
            author=self.user,
            content="답변",
        )

        response = self.client.get(self.url, {"answered": True})

        self.assertEqual(len(response.data["results"]), 1)

        question_data = response.data["results"][0]
        self.assertGreater(question_data["answer_count"], 0)

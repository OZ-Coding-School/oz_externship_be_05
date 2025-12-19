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

    # QuerySerializer 자체 검증 실패 400
    def test_query_serializer_validation_error_message(self) -> None:
        response = self.client.get(self.url, {"page": 0})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error_detail"],
            "유효하지 않은 목록 조회 요청입니다.",
        )
        self.assertIn("errors", response.data)

    # 잘못된 페이지 요청 400
    def test_question_list_invalid_page_returns_400(self) -> None:
        Question.objects.create(
            author=self.user,
            category=self.category,
            title="테스트 질문",
            content="내용",
        )
        response = self.client.get(self.url, {"page": 999})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["errors"],
            {"page": ["유효하지 않은 페이지입니다."]},
        )
        self.assertIn("error_detail", response.data)

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
        item = response.data["questions"][0]

        self.assertIn("answer_count", item)
        self.assertEqual(item["answer_count"], 0)

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

        self.assertEqual(len(response.data["questions"]), 1)
        self.assertGreater(response.data["questions"][0]["answer_count"], 0)

    # answered=false 필터
    def test_answered_filter_false(self) -> None:
        Question.objects.create(
            author=self.user,
            title="미답변 질문",
            content="내용",
            category=self.category,
        )

        response = self.client.get(self.url, {"answered": False})

        self.assertEqual(len(response.data["questions"]), 1)
        self.assertEqual(response.data["questions"][0]["answer_count"], 0)

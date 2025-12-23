from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.qna.models import Question, QuestionCategory
from apps.user.models import User
from apps.user.models.user import RoleChoices


class QuestionDetailAPITests(APITestCase):

    # 존재하지 않는 질문 → 404
    def test_question_not_found_returns_404(self) -> None:
        url = reverse("question_detail", kwargs={"question_id": 9999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 정상 조회
    def test_question_detail_success(self) -> None:
        user = User.objects.create_user(
            email="servicetest@test.com",
            password="test1234",
            name="서비스 테스트 유저",
            role=RoleChoices.ST,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
        )

        category = QuestionCategory.objects.create(name="Backend")

        question = Question.objects.create(
            author=user,
            category=category,
            title="상세 질문",
            content="상세 내용",
        )

        url = reverse("question_detail", kwargs={"question_id": question.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "상세 질문")

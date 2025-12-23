from django.test import TestCase

from apps.qna.exceptions.question_exceptions import QuestionNotFoundError
from apps.qna.models import Question, QuestionCategory
from apps.qna.services.question.question_detail.service import (
    get_question_detail,
)
from apps.user.models import User
from apps.user.models.user import RoleChoices


class QuestionDetailServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="service@test.com",
            password="test1234",
            name="서비스유저",
            role=RoleChoices.ST,
            phone_number="010-2222-2222",
            gender="M",
            birthday="2000-01-01",
        )

        self.category = QuestionCategory.objects.create(name="Backend")

        self.question = Question.objects.create(
            author=self.user,
            title="서비스 질문",
            content="서비스 내용",
            category=self.category,
        )

    # 조회수 테스트
    def test_question_not_found(self) -> None:
        with self.assertRaises(QuestionNotFoundError):
            get_question_detail(question_id=9999)

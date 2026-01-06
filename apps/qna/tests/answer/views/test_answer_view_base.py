import datetime

from rest_framework.test import APITestCase

from apps.qna.models.question import Question, QuestionCategory
from apps.user.models.user import RoleChoices, User


class _AnswerViewDBBase(APITestCase):
    """Answer View 테스트용 DB 기본 데이터"""

    user: User
    other_user: User
    password: str
    question_category: QuestionCategory
    question: Question

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="testuser",
            nickname="테스터",
            role=RoleChoices.ST,
            birthday=datetime.date(2000, 1, 1),
        )
        cls.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            name="otheruser",
            nickname="다른유저",
            role=RoleChoices.ST,
            birthday=datetime.date(2000, 1, 1),
        )
        cls.question_category = QuestionCategory.objects.create(
            name="test_category",
        )
        cls.question = Question.objects.create(
            author=cls.user,
            category=cls.question_category,
            title="테스트 질문",
            content="질문 내용입니다.",
        )

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)

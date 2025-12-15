from django.test import TestCase

from apps.qna.exceptions.question_exceptions import (
    CategoryNotFoundError,
)
from apps.qna.models import Question, QuestionCategory, QuestionImage
from apps.qna.services.question.question_create_service import (
    create_question,
    get_category_or_raise,
)
from apps.user.models import RoleChoices, User


class QuestionCreateServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="servicetest@test.com",
            password="test1234",
            name="서비스 테스트 유저",
            role=RoleChoices.ST,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
        )

        self.category = QuestionCategory.objects.create(name="백엔드")

    # 질문 생성 성공
    def test_create_question_success(self) -> None:
        question = create_question(
            author=self.user,
            category=self.category,
            validated_data={
                "title": "질문 제목",
                "content": "질문 내용",
                "image_urls": ["https://test.com/img1.png"],
            },
        )

        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(QuestionImage.objects.count(), 1)
        self.assertEqual(question.title, "질문 제목")

    # 404 존재하지 않는 카테고리 ID
    def test_category_not_found_raises_404_error(self) -> None:
        with self.assertRaises(CategoryNotFoundError):
            get_category_or_raise(9999)

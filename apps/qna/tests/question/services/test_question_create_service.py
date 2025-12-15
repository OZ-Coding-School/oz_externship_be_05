from django.test import TestCase

from apps.qna.exceptions.question_exceptions import (
    CategoryNotFoundError,
    DuplicateQuestionTitleError,
)
from apps.qna.models import Question, QuestionCategory, QuestionImage
from apps.qna.services.question.question_create_service import create_question
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
            title="질문 제목",
            content="질문 내용",
            category_id=self.category.id,
            image_urls=["https://test.com/img1.png"],
        )

        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(QuestionImage.objects.count(), 1)
        self.assertEqual(question.title, "질문 제목")

    # 409 제목 중복
    def test_duplicate_title_raises_409_error(self) -> None:
        Question.objects.create(
            author=self.user,
            title="중복 질문",
            content="내용",
            category=self.category,
        )

        with self.assertRaises(DuplicateQuestionTitleError):
            create_question(
                author=self.user,
                title="중복 질문",
                content="다른 내용",
                category_id=self.category.id,
                image_urls=[],
            )

    # 404 존재하지 않는 카테고리 ID
    def test_category_not_found_raises_404_error(self) -> None:
        with self.assertRaises(CategoryNotFoundError):
            create_question(
                author=self.user,
                title="카테고리 없음",
                content="내용",
                category_id=9999,
                image_urls=[],
            )

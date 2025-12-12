from django.test import TestCase

from apps.qna.models import Question, QuestionCategory, QuestionImage
from apps.qna.services.question.question_create_service import create_question
from apps.user.models import RoleChoices, User


# 질문 + 이미지 생성 성공
class QuestionCreateServiceTests(TestCase):
    def setUp(self) -> None:
        self.category = QuestionCategory.objects.create(name="프론트엔드")

        self.student = User.objects.create_user(
            email="student@test.com",
            password="test1234",
            name="학생",
            role=RoleChoices.ST,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
        )

    def test_create_question_with_images(self) -> None:
        question = create_question(
            author=self.student,
            title="서비스 테스트",
            content="내용",
            category=self.category,
            image_urls=[
                "https://test.com/1.png",
                "https://test.com/2.png",
            ],
        )

        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(question.title, "서비스 테스트")
        self.assertEqual(QuestionImage.objects.count(), 2)

    # 이미지 없이도 정상 생성
    def test_create_question_without_images(self) -> None:
        question = create_question(
            author=self.student,
            title="이미지 없음",
            content="내용",
            category=self.category,
            image_urls=[],
        )

        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(QuestionImage.objects.count(), 0)

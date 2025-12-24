from django.test import TestCase

from apps.qna.models import Question, QuestionCategory
from apps.qna.services.question.question_update.service import update_question
from apps.user.models import User
from apps.user.models.user import RoleChoices


class QuestionUpdateServiceTest(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="user@test.com",
            password="1234",
            name="유저",
            role=RoleChoices.ST,
            phone_number="010-3333-3333",
            gender="M",
            birthday="1998-01-01",
        )

        self.category = QuestionCategory.objects.create(
            name="카테고리",
        )

        self.question = Question.objects.create(
            author=self.user,
            title="기존 제목",
            content="기존 내용",
            category=self.category,
        )

    # 내용만 수정
    def test_update_content_only(self) -> None:
        update_question(
            question=self.question,
            validated_data={"content": "변경된 내용"},
        )

        self.question.refresh_from_db()
        self.assertEqual(self.question.content, "변경된 내용")

    # 이미지 추가
    def test_add_image(self) -> None:
        update_question(
            question=self.question,
            validated_data={
                "images": {
                    "add_urls": ["https://img.com/1.png"],
                }
            },
        )

        self.assertEqual(self.question.images.count(), 1)

    # 변경된 부분만 업데이트
    def test_only_updated_field_is_changed(self) -> None:
        update_question(
            question=self.question,
            validated_data={
                "title": "변경된 제목",
            },
        )

        self.question.refresh_from_db()

        # 변경된 필드
        self.assertEqual(self.question.title, "변경된 제목")

        # 변경되지 않은 필드
        self.assertEqual(self.question.content, "기존 내용")
        self.assertEqual(self.question.category, self.category)

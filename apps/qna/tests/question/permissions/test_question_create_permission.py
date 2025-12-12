from typing import Any, cast

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.qna.models import Question, QuestionCategory
from apps.qna.permissions.question.question_create_permission import (
    validate_question_create_permission,
    validate_question_title_unique,
)
from apps.user.models import RoleChoices, User


# 학생권한이 아닌 경우 권한 실패
class QuestionCreatePermissionValidatorTests(TestCase):
    def test_permission_fail_when_not_student(self) -> None:
        user = User.objects.create_user(
            email="user@test.com",
            password="test1234",
            name="일반유저",
            role=RoleChoices.USER,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
        )

        with self.assertRaises(ValidationError) as context:
            validate_question_create_permission(user)

        self.assertEqual(cast(dict[str, Any], context.exception.detail)["type"], "permission_denied")


# 제목 중복일 때 실패
class QuestionCreateTitleValidatorTests(TestCase):
    def setUp(self) -> None:
        self.category = QuestionCategory.objects.create(name="백엔드")

        self.user = User.objects.create_user(
            email="student@test.com",
            password="test1234",
            name="학생",
            role=RoleChoices.ST,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
        )

        Question.objects.create(
            author=self.user,
            category=self.category,
            title="중복 제목",
            content="내용",
        )

    def test_title_conflict(self) -> None:
        with self.assertRaises(ValidationError) as context:
            validate_question_title_unique("중복 제목")

        self.assertEqual(cast(dict[str, Any], context.exception.detail)["type"], "title_conflict")

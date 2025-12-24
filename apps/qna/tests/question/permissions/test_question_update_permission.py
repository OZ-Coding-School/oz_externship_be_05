from typing import Any, cast

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.exceptions.exception_messages import EMS
from apps.qna.models import Question, QuestionCategory
from apps.user.models import User
from apps.user.models.user import RoleChoices


class QuestionUpdatePermissionTest(APITestCase):

    def setUp(self) -> None:
        self.author = User.objects.create_user(
            email="author@test.com",
            password="1234",
            name="작성자",
            role=RoleChoices.ST,
            phone_number="010-1111-1111",
            gender="M",
            birthday="1999-01-01",
        )
        self.other_user = User.objects.create_user(
            email="other@test.com",
            password="1234",
            name="다른유저",
            role=RoleChoices.ST,
            phone_number="010-2222-2222",
            gender="M",
            birthday="1999-01-01",
        )

        self.non_student = User.objects.create_user(
            email="admin@test.com",
            password="1234",
            name="관리자",
            role=RoleChoices.AD,  # 학생 아님
            phone_number="010-9999-9999",
            gender="M",
            birthday="1990-01-01",
        )

        self.category = QuestionCategory.objects.create(
            name="카테고리",
        )

        self.question = Question.objects.create(
            author=self.author,
            title="질문",
            content="내용",
            category=self.category,
        )

        self.url = reverse("question_detail", args=[self.question.id])

    # 403: 질문 작성자 != 현재 유저
    def test_non_owner_cannot_update(self) -> None:
        self.client.force_authenticate(self.other_user)

        response = self.client.patch(
            self.url,
            {"title": "해킹 시도"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        data = cast(dict[str, Any], response.data)

        self.assertEqual(
            data["error_detail"],
            EMS.E403_OWNER_ONLY_EDIT("질문")["error_detail"],
        )

    # 403: 로그인 O + 학생 X
    def test_non_student_with_correct_message(self) -> None:
        self.client.force_authenticate(self.non_student)

        response = self.client.patch(
            self.url,
            {"title": "수정 시도"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        data = cast(dict[str, Any], response.data)

        self.assertEqual(
            data["error_detail"],
            EMS.E403_QNA_PERMISSION_DENIED("등록")["error_detail"],
        )

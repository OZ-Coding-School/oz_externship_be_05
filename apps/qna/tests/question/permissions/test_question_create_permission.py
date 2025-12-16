from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from apps.qna.permissions.question.question_create_permission import (
    QuestionCreatePermission,
)
from apps.user.models.user import RoleChoices, User


class QuestionCreatePermissionTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.permission = QuestionCreatePermission()

    def create_user(self, role: RoleChoices) -> User:
        return User.objects.create_user(
            email="permissiontest@test.com",
            password="test1234",
            name="권한 테스트 유저",
            role=role,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
        )

    # 성공: 학생 권한
    def test_student_has_permission(self) -> None:
        user = self.create_user(RoleChoices.ST)
        request = self.factory.post("/api/v1/qna/questions")
        request.user = user

        view = APIView()
        self.assertTrue(self.permission.has_permission(request, view))

    # 실패: 학생이 아닌 권한
    def test_non_student_has_no_permission(self) -> None:
        user = self.create_user(RoleChoices.USER)
        request = self.factory.post("/api/v1/qna/questions")
        request.user = user

        view = APIView()
        self.assertFalse(self.permission.has_permission(request, view))

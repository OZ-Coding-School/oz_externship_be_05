from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.qna.models import QuestionCategory
from apps.user.models.user import RoleChoices, User


class QuestionCreateAPITests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("question_create")
        self.category = QuestionCategory.objects.create(name="백엔드")

    def create_user(self, role: RoleChoices) -> User:
        return User.objects.create_user(
            email="apitest@test.com",
            password="test1234",
            name="유저",
            role=role,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
        )

    # 질문 생성 성공
    def test_question_create_success(self) -> None:
        user = self.create_user(RoleChoices.ST)
        self.client.force_authenticate(user=user)

        payload = {
            "title": "질문 등록",
            "content": "내용입니다",
            "category": self.category.id,
            "image_urls": ["https://test.com/img.png"],
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("question_id", response.data)

    # 401 로그인 체크
    def test_unauthenticated_user_gets_401(self) -> None:
        payload = {
            "title": "질문",
            "content": "내용",
            "category": self.category.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["error_detail"],
            "로그인한 수강생만 질문을 등록할 수 있습니다.",
        )

    # 403 Role가 학생이 아닌 경우
    def test_non_student_user_gets_403(self) -> None:
        user = self.create_user(RoleChoices.USER)
        self.client.force_authenticate(user=user)

        payload = {
            "title": "질문",
            "content": "내용",
            "category": self.category.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 400 제목이 없음
    def test_invalid_payload_gets_400(self) -> None:
        user = self.create_user(RoleChoices.ST)
        self.client.force_authenticate(user=user)

        payload = {
            "content": "제목 없음",
            "category": self.category.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error_detail"],
            "유효하지 않은 질문 등록 요청입니다.",
        )

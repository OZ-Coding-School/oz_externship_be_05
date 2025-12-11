from typing import Any

from rest_framework import status
from rest_framework.test import APITestCase

from apps.questions.models import QuestionCategory
from apps.user.models import RoleChoices, User


class QuestionCreateAPITests(APITestCase):
    def setUp(self) -> None:
        # 테스트용 카테고리 생성
        self.category = QuestionCategory.objects.create(name="프론트엔드")

        # API URL
        self.url = "/api/v1/qna/questions"

    def create_test_user(self, **kwargs: Any) -> User:
        default_data = {
            "phone_number": "010-0000-0000",
            "gender": "M",
            "birthday": "2000-01-01",
        }
        default_data.update(kwargs)
        return User.objects.create_user(**default_data)

    # 성공 케이스
    def test_question_create_success(self) -> None:
        student = self.create_test_user(
            email="student@test.com",
            password="test1234",
            name="학생A",
            role=RoleChoices.ST,
        )

        # 인증 설정
        self.client.force_authenticate(user=student)

        payload = {
            "title": "정상 등록 테스트",
            "content": "내용",
            "category": self.category.id,
            "image_urls": ["https://test.com/img.png"],
        }

        response = self.client.post(self.url, payload, format="json")

        # 검증
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("question_id", response.data)

    # 유효성 검사 실패 케이스
    def test_question_create_validation_fail(self) -> None:
        student = self.create_test_user(
            email="student2@test.com",
            password="test1234",
            name="학생B",
            role=RoleChoices.ST,
        )
        self.client.force_authenticate(user=student)

        payload = {
            "title": "",  # 빈 값
            "content": "",
            "category": None,  # 존재하지 않는 카테고리
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 권한 실패 케이스
    def test_question_create_permission_fail(self) -> None:
        normal_user = self.create_test_user(
            email="normal@test.com",
            password="test1234",
            name="일반유저",
            role=RoleChoices.USER,  # 학생(ST) 아님
        )
        self.client.force_authenticate(user=normal_user)

        payload = {
            "title": "권한 실패 테스트",
            "content": "내용",
            "category": self.category.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

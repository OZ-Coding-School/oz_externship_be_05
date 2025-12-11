from typing import Any

from rest_framework import status
from rest_framework.test import APITestCase

from apps.questions.models import Question, QuestionCategory
from apps.user.models import RoleChoices, User


class QuestionCreateAPITests(APITestCase):
    def setUp(self) -> None:
        self.category = QuestionCategory.objects.create(name="프론트엔드")
        self.url = "/api/v1/qna/questions"

    def create_test_user(self, **kwargs: Any) -> User:
        default_data = {
            "phone_number": "010-0000-0000",
            "gender": "M",
            "birthday": "2000-01-12",
        }
        default_data.update(kwargs)
        return User.objects.create_user(**default_data)

    # 1) 성공 케이스 → 201
    def test_question_create_success(self) -> None:
        student = self.create_test_user(
            email="student@test.com",
            password="test1234",
            name="학생A",
            role=RoleChoices.ST,
        )
        self.client.force_authenticate(user=student)

        payload = {
            "title": "정상 등록 테스트",
            "content": "내용",
            "category": self.category.id,
            "image_urls": ["https://test.com/img.png"],
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("question_id", response.data)

    # 2) 유효성 실패 → 400
    def test_question_create_validation_fail(self) -> None:
        student = self.create_test_user(
            email="student2@test.com",
            password="test1234",
            name="학생B",
            role=RoleChoices.ST,
        )
        self.client.force_authenticate(user=student)

        payload = {
            "title": "",  # 비어있으면 X
            "content": "",
            "category": None,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 3) 권한 실패 → 403
    def test_question_create_permission_fail(self) -> None:
        normal_user = self.create_test_user(
            email="normal@test.com",
            password="test1234",
            name="일반유저",
            role=RoleChoices.USER,  # ST 아님
        )
        self.client.force_authenticate(user=normal_user)

        payload = {
            "title": "권한 실패 테스트",
            "content": "내용",
            "category": self.category.id,
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 4) 제목 중복 → 409
    def test_question_create_title_conflict(self) -> None:
        student = self.create_test_user(
            email="student3@test.com",
            password="test1234",
            name="학생C",
            role=RoleChoices.ST,
        )
        self.client.force_authenticate(user=student)

        # 질문
        Question.objects.create(
            author=student,
            category=self.category,
            title="중복 제목",
            content="내용",
        )

        # 같은 제목으로 요청
        payload = {
            "title": "중복 제목",
            "content": "다른 내용",
            "category": self.category.id,
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    # 5) 존재하지 않는 category → 404
    def test_question_create_invalid_category(self) -> None:
        student = self.create_test_user(
            email="student4@test.com",
            password="test1234",
            name="학생D",
            role=RoleChoices.ST,
        )
        self.client.force_authenticate(user=student)

        payload = {
            "title": "카테고리 실패 테스트",
            "content": "내용",
            "category": 9999,  # 존재하지 않는 ID
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 6) image_urls 미포함해도 정상 생성
    def test_question_create_without_image_urls(self) -> None:
        student = self.create_test_user(
            email="student5@test.com",
            password="test1234",
            name="학생E",
            role=RoleChoices.ST,
        )
        self.client.force_authenticate(user=student)

        payload = {
            "title": "이미지 없이 생성",
            "content": "내용",
            "category": self.category.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("question_id", response.data)

    # 7) image_urls 빈 리스트여도 정상
    def test_question_create_empty_image_urls(self) -> None:
        student = self.create_test_user(
            email="student6@test.com",
            password="test1234",
            name="학생F",
            role=RoleChoices.ST,
        )
        self.client.force_authenticate(user=student)

        payload = {
            "title": "빈 이미지 리스트 테스트",
            "content": "내용",
            "category": self.category.id,
            "image_urls": [],
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

from typing import Any

from rest_framework import status
from rest_framework.test import APITestCase

from apps.qna.models import Question, QuestionCategory, QuestionImage
from apps.user.models import RoleChoices, User


class QuestionCreateAPITests(APITestCase):
    def setUp(self) -> None:
        self.category = QuestionCategory.objects.create(name="프론트엔드")
        self.url = "/api/v1/qna/questions"

    def create_test_user(self, **kwargs: Any) -> User:
        default = {
            "phone_number": "010-0000-0000",
            "gender": "M",
            "birthday": "2000-01-12",
        }
        default.update(kwargs)
        return User.objects.create_user(**default)

    # 1) 정상 생성
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
        self.assertTrue(QuestionImage.objects.filter(question_id=response.data["question_id"]).exists())

    # 2) 400 - title / content / category 없는 경우
    def test_question_create_validation_fail(self) -> None:
        student = self.create_test_user(
            email="student2@test.com",
            password="test1234",
            name="학생B",
            role=RoleChoices.ST,
        )
        self.client.force_authenticate(user=student)

        payload = {"title": "", "content": "", "category": None}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 3) 403 - 학생(ST) 아님
    def test_question_create_permission_fail(self) -> None:
        user = self.create_test_user(
            email="normal@test.com",
            password="test1234",
            name="일반유저",
            role=RoleChoices.USER,
        )
        self.client.force_authenticate(user=user)

        payload = {"title": "권한 실패", "content": "내용", "category": self.category.id}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "질문 등록 권한이 없습니다.")

    # 4) 409 - 제목 중복
    def test_question_create_title_conflict(self) -> None:
        student = self.create_test_user(
            email="student3@test.com",
            password="test1234",
            name="학생C",
            role=RoleChoices.ST,
        )
        self.client.force_authenticate(user=student)

        Question.objects.create(
            author=student,
            category=self.category,
            title="중복 제목",
            content="내용",
        )

        payload = {"title": "중복 제목", "content": "다른", "category": self.category.id}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["error_detail"], "중복된 질문 제목이 이미 존재합니다.")

    # 5) 404 - 존재하지 않는 카테고리
    def test_question_create_invalid_category(self) -> None:
        student = self.create_test_user(
            email="student4@test.com",
            password="test1234",
            name="학생D",
            role=RoleChoices.ST,
        )
        self.client.force_authenticate(user=student)

        payload = {"title": "카테고리 실패", "content": "내용", "category": 9999}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "선택한 카테고리를 찾을 수 없습니다.")

    # 6) image_urls 없어도 정상
    def test_question_create_without_image_urls(self) -> None:
        student = self.create_test_user(
            email="student5@test.com",
            password="test1234",
            name="학생E",
            role=RoleChoices.ST,
        )
        self.client.force_authenticate(user=student)

        payload = {"title": "이미지 없음", "content": "내용", "category": self.category.id}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # 7) image_urls = [] 여도 정상
    def test_question_create_empty_image_urls(self) -> None:
        student = self.create_test_user(
            email="student6@test.com",
            password="test1234",
            name="학생F",
            role=RoleChoices.ST,
        )
        self.client.force_authenticate(user=student)

        payload = {
            "title": "빈 이미지 리스트",
            "content": "내용",
            "category": self.category.id,
            "image_urls": [],
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

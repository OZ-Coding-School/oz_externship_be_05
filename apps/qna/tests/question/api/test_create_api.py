from unittest import mock
from unittest.mock import MagicMock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.exceptions.exception_messages import EMS
from apps.qna.models import QuestionCategory, QuestionImage
from apps.user.models.user import RoleChoices, User


class QuestionCreateAPITests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("questions")
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
    @mock.patch("apps.qna.services.common.image_service.S3Client")
    def test_question_create_success(self, mock_s3_client_class: MagicMock) -> None:
        mock_s3_instance = mock_s3_client_class.return_value
        mock_s3_instance.is_valid_s3_url.return_value = True

        user = self.create_user(RoleChoices.ST)
        self.client.force_authenticate(user=user)

        img_url = "https://test.com/img.png"
        payload = {
            "title": "질문 등록",
            "content": f'내용입니다 <img src="{img_url}">',
            "category": self.category.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("question_id", response.data)

        # 실제 DB에 이미지가 생성되었는지 확인
        self.assertEqual(QuestionImage.objects.count(), 1)
        image = QuestionImage.objects.first()
        assert image is not None
        self.assertEqual(image.img_url, img_url)

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
            EMS.E401_STUDENT_ONLY_ACTION("질문을 등록")["error_detail"],
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
        self.assertEqual(
            response.data["error_detail"],
            EMS.E403_QNA_PERMISSION_DENIED("등록")["error_detail"],
        )

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
            EMS.E400_INVALID_REQUEST("질문 등록")["error_detail"],
        )

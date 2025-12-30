from typing import Any
from unittest import mock
from unittest.mock import MagicMock

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.exceptions.exception_messages import EMS
from apps.qna.models import QuestionCategory, QuestionImage
from apps.qna.services.question.question_create_service import create_question
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
    @mock.patch("apps.qna.services.question.question_image_service.S3Client")  # 경로 수정
    @override_settings(AWS_S3_BUCKET_NAME="test-bucket")  # 버킷명 설정 추가
    def test_question_create_success(self, mock_s3_client_class: MagicMock) -> None:
        mock_s3_instance = mock_s3_client_class.return_value
        # 유효한 S3 URL 형식 사용
        valid_url = "https://test-bucket.s3.ap-northeast-2.amazonaws.com/question_images/test.jpg"

        user = self.create_user(RoleChoices.ST)
        self.client.force_authenticate(user=user)

        payload = {
            "title": "질문 등록",
            "content": f'내용입니다 <img src="{valid_url}">',  # 유효 URL 적용
            "category": self.category.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Key('question_images/test.jpg')가 저장
        self.assertEqual(QuestionImage.objects.count(), 1)
        image = QuestionImage.objects.first()
        self.assertIsNotNone(image)
        if image:
            self.assertEqual(image.img_url, "question_images/test.jpg")

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

    @override_settings(AWS_S3_BUCKET_NAME="test-bucket")
    def test_create_question_with_mixed_images(self) -> None:
        """S3 이미지와 외부 이미지가 섞여 있을 때 S3 이미지만 저장되는지 테스트"""
        s3_url = "https://test-bucket.s3.ap-northeast-2.amazonaws.com/question_images/my-s3.jpg"
        external_url = "https://naver.com/logo.png"
        user = self.create_user(RoleChoices.ST)

        # S3 이미지와 외부 이미지가 모두 포함된 본문
        content = f'<img src="{s3_url}"> <img src="{external_url}">'

        data: dict[str, Any] = {
            "title": "혼합 이미지 테스트",
            "content": content,
        }

        create_question(author=user, category=self.category, validated_data=data)

        # DB에는 S3 이미지 1개만 Key로 저장되어야 함
        self.assertEqual(QuestionImage.objects.count(), 1)
        image = QuestionImage.objects.first()
        self.assertIsNotNone(image)
        if image:
            self.assertEqual(image.img_url, "question_images/my-s3.jpg")
            self.assertNotIn("naver.com", image.img_url)

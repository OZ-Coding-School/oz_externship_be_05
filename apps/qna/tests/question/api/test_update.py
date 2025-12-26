from typing import Any, cast
from unittest import mock
from unittest.mock import MagicMock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.qna.models import Question, QuestionCategory, QuestionImage
from apps.user.models import User
from apps.user.models.user import RoleChoices


class QuestionUpdateAPITest(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@test.com",
            password="test1234",
            name="테스트 유저",
            role=RoleChoices.ST,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-12",
        )
        self.client.force_authenticate(self.user)

        self.category = QuestionCategory.objects.create(
            name="Backend",
        )

        self.question = Question.objects.create(
            author=self.user,
            title="기존 제목",
            content="기존 내용",
            category=self.category,
        )

        # 이미지 3개 생성
        self.urls = [
            "https://img.com/1.png",
            "https://img.com/2.png",
            "https://img.com/3.png",
        ]
        self.images = [QuestionImage.objects.create(question=self.question, img_url=url) for url in self.urls]

        self.url = reverse("question_detail", args=[self.question.id])

    # 200: 부분 수정 (제목만)
    def test_partial_update_title(self) -> None:
        response = self.client.patch(
            self.url,
            {"title": "수정된 제목"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.question.refresh_from_db()
        self.assertEqual(self.question.title, "수정된 제목")

    # 200: 이미지 1개 삭제, 1개 등록
    @mock.patch("apps.qna.services.common.image_service.S3Client")
    def test_update_image_delete_and_add(self, mock_s3_client_class: MagicMock) -> None:
        mock_s3_instance = mock_s3_client_class.return_value
        mock_s3_instance.is_valid_s3_url.return_value = True

        # 기존 이미지 1번 삭제 / 2,3번 유지 / 4번 추가
        new_url = "https://new.com/4.png"

        # 1번(urls[0]) 제외, 2번(urls[1]), 3번(urls[2]) 유지, 4번 추가
        new_content = f"""
            <p>내용 수정</p>
            <img src="{self.urls[1]}">
            <img src="{self.urls[2]}">
            <img src="{new_url}">
        """

        response = self.client.patch(
            self.url,
            {"content": new_content},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # DB 검증
        current_urls = set(QuestionImage.objects.filter(question=self.question).values_list("img_url", flat=True))

        self.assertNotIn(self.urls[0], current_urls)  # 1번 삭제됨
        self.assertIn(self.urls[1], current_urls)  # 2번 유지
        self.assertIn(self.urls[2], current_urls)  # 3번 유지
        self.assertIn(new_url, current_urls)  # 4번 추가됨

        # S3 삭제 호출 검증
        mock_s3_instance.delete_from_url.assert_called_with(self.urls[0])

    # 200: 이미지 전부 삭제
    @mock.patch("apps.qna.services.common.image_service.S3Client")
    def test_delete_all_images(self, mock_s3_client_class: MagicMock) -> None:
        mock_s3_instance = mock_s3_client_class.return_value

        response = self.client.patch(
            self.url,
            {"content": "이미지 싹 지움"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.question.images.count(), 0)

        # 3개 모두 삭제 호출되었는지 확인
        self.assertEqual(mock_s3_instance.delete_from_url.call_count, 3)

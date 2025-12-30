from typing import Any
from unittest import mock
from unittest.mock import MagicMock

from django.test import override_settings  # [수정] settings 제어를 위해 추가
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

        # 유효성 검사를 통과할 수 있는 S3 URL 패턴으로 정의
        self.bucket_name = "test-bucket"
        self.urls = [
            f"https://{self.bucket_name}.s3.ap-northeast-2.amazonaws.com/question_images/1.png",
            f"https://{self.bucket_name}.s3.ap-northeast-2.amazonaws.com/question_images/2.png",
            f"https://{self.bucket_name}.s3.ap-northeast-2.amazonaws.com/question_images/3.png",
        ]
        # DB에는 Key만 저장됨
        self.keys = ["question_images/1.png", "question_images/2.png", "question_images/3.png"]
        self.images = [QuestionImage.objects.create(question=self.question, img_url=key) for key in self.keys]

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
    @override_settings(AWS_S3_BUCKET_NAME="test-bucket")
    @mock.patch("apps.qna.services.question.question_image_service.transaction.on_commit")
    @mock.patch("apps.qna.services.question.question_image_service.S3Client")
    def test_update_image_delete_and_add(self, mock_s3_client_class: MagicMock, mock_on_commit: MagicMock) -> None:
        mock_s3_instance = mock_s3_client_class.return_value

        # [수정] 트랜잭션 commit 시 내부 함수(삭제 로직)를 즉시 실행하도록 설정
        mock_on_commit.side_effect = lambda func: func()

        # 기존 이미지 1번 삭제 / 2,3번 유지 / 4번 추가
        new_url = f"https://{self.bucket_name}.s3.ap-northeast-2.amazonaws.com/question_images/4.png"

        # 1번 제외, 2번, 3번 유지, 4번 추가
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

        # DB 검증: Key 기준으로 확인
        current_keys = set(QuestionImage.objects.filter(question=self.question).values_list("img_url", flat=True))

        self.assertNotIn(self.keys[0], current_keys)  # 1번 삭제됨
        self.assertIn(self.keys[1], current_keys)  # 2번 유지
        self.assertIn(self.keys[2], current_keys)  # 3번 유지
        self.assertIn("question_images/4.png", current_keys)  # 4번 추가됨

        # [수정] delete_from_url이 아닌 delete 메서드와 Key 인자 확인
        mock_s3_instance.delete.assert_called_with(self.keys[0])

    # 200: 이미지 전부 삭제
    @override_settings(AWS_S3_BUCKET_NAME="test-bucket")
    @mock.patch("apps.qna.services.question.question_image_service.transaction.on_commit")  # [수정] 패치 추가
    @mock.patch("apps.qna.services.question.question_image_service.S3Client")
    def test_delete_all_images(self, mock_s3_client_class: MagicMock, mock_on_commit: MagicMock) -> None:
        mock_s3_instance = mock_s3_client_class.return_value
        mock_on_commit.side_effect = lambda func: func()

        response = self.client.patch(
            self.url,
            {"content": "이미지 싹 지움"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.question.images.count(), 0)

        # [수정] delete_from_url -> delete 명칭 수정
        self.assertEqual(mock_s3_instance.delete.call_count, 3)

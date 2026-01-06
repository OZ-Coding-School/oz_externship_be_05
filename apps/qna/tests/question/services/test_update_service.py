from unittest import mock
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from apps.qna.models import Question, QuestionCategory, QuestionImage
from apps.qna.services.question.question_update.service import update_question
from apps.user.models import User
from apps.user.models.user import RoleChoices


class QuestionUpdateServiceTest(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="user@test.com",
            password="1234",
            name="유저",
            role=RoleChoices.ST,
            phone_number="010-3333-3333",
            gender="M",
            birthday="1998-01-01",
        )

        self.category = QuestionCategory.objects.create(
            name="카테고리",
        )

        self.question = Question.objects.create(
            author=self.user,
            title="기존 제목",
            content="기존 내용",
            category=self.category,
        )

        self.valid_s3_url = "https://test-bucket.s3.ap-northeast-2.amazonaws.com/question_images/new.jpg"

    # 내용만 수정
    def test_update_content_only(self) -> None:
        update_question(
            question=self.question,
            validated_data={"content": "변경된 내용"},
        )

        self.question.refresh_from_db()
        self.assertEqual(self.question.content, "변경된 내용")

    # 이미지 추가 (본문에 태그 추가)
    @override_settings(AWS_S3_BUCKET_NAME="test-bucket")
    @mock.patch("apps.qna.services.question.question_image_service.S3Client")
    def test_add_image_via_content(self, mock_s3_client_class: MagicMock) -> None:
        mock_s3_instance = mock_s3_client_class.return_value

        new_content = f'이미지 추가됨 <img src="{self.valid_s3_url}">'

        update_question(
            question=self.question,
            validated_data={"content": new_content},
        )

        # DB 검증: 1개가 생성되어야 하며 URL이 아닌 Key로 저장되어야 함
        self.assertEqual(self.question.images.count(), 1)
        image = self.question.images.first()
        self.assertIsNotNone(image)
        if image:
            self.assertEqual(image.img_url, "question_images/new.jpg")

    # 이미지 삭제 (본문에서 태그 제거)
    @patch("apps.qna.services.question.question_image_service.transaction.on_commit")  # 경로 수정
    @patch("apps.core.utils.s3_client.S3Client.delete")  # 메서드 수정
    def test_delete_image_via_content(self, mock_s3_delete: MagicMock, mock_on_commit: MagicMock) -> None:
        old_key = "question_images/old.jpg"
        QuestionImage.objects.create(question=self.question, img_url=old_key)

        # 트랜잭션 즉시 실행
        mock_on_commit.side_effect = lambda func: func()

        update_question(
            question=self.question,
            validated_data={"content": "이제 이미지가 없습니다."},
        )

        self.assertEqual(self.question.images.count(), 0)
        mock_s3_delete.assert_called_once_with(old_key)

    # 변경된 부분만 업데이트
    def test_only_updated_field_is_changed(self) -> None:
        update_question(
            question=self.question,
            validated_data={
                "title": "변경된 제목",
            },
        )

        self.question.refresh_from_db()
        self.assertEqual(self.question.title, "변경된 제목")
        self.assertEqual(self.question.content, "기존 내용")

from unittest import mock
from unittest.mock import MagicMock

from django.test import TestCase

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

    # 내용만 수정
    def test_update_content_only(self) -> None:
        update_question(
            question=self.question,
            validated_data={"content": "변경된 내용"},
        )

        self.question.refresh_from_db()
        self.assertEqual(self.question.content, "변경된 내용")

    # 이미지 추가 (본문에 태그 추가)
    @mock.patch("apps.qna.services.common.image_service.S3Client")
    def test_add_image_via_content(self, mock_s3_client_class: MagicMock) -> None:
        mock_s3_instance = mock_s3_client_class.return_value
        mock_s3_instance.is_valid_s3_url.return_value = True

        new_url = "https://img.com/1.png"
        new_content = f'이미지 추가됨 <img src="{new_url}">'

        update_question(
            question=self.question,
            validated_data={"content": new_content},
        )

        self.assertEqual(self.question.images.count(), 1)
        image = self.question.images.first()
        assert image is not None
        self.assertEqual(image.img_url, new_url)

    # 이미지 삭제 (본문에서 태그 제거)
    @mock.patch("apps.qna.services.common.image_service.S3Client")
    def test_delete_image_via_content(self, mock_s3_client_class: MagicMock) -> None:
        # 이미지가 있는 상태로 시작
        existing_url = "https://img.com/exist.png"
        QuestionImage.objects.create(question=self.question, img_url=existing_url)

        mock_s3_instance = mock_s3_client_class.return_value

        # 이미지가 없는 텍스트로 본문 수정
        update_question(
            question=self.question,
            validated_data={"content": "이제 이미지가 없습니다."},
        )

        self.assertEqual(self.question.images.count(), 0)
        # S3 삭제 로직이 호출되었는지 확인
        mock_s3_instance.delete_from_url.assert_called_once_with(existing_url)

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

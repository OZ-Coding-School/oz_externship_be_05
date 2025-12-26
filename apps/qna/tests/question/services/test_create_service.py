from unittest import mock
from unittest.mock import MagicMock

from django.test import TestCase

from apps.qna.models import Question, QuestionCategory, QuestionImage
from apps.qna.services.question.question_create_service import create_question
from apps.user.models.user import RoleChoices, User


class QuestionCreateServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="servicetest@test.com",
            password="test1234",
            name="서비스 테스트 유저",
            role=RoleChoices.ST,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
        )

        self.category = QuestionCategory.objects.create(name="백엔드")

    # S3 Client를 Mocking하여 실제 S3 통신 없이 테스트 수행
    @mock.patch("apps.qna.services.common.image_service.S3Client")
    def test_create_question_success(self, mock_s3_client_class: MagicMock) -> None:

        # S3 URL 검증이 무조건 True를 반환하도록 설정
        mock_s3_instance = mock_s3_client_class.return_value
        mock_s3_instance.is_valid_s3_url.return_value = True

        # 본문에 이미지 태그를 포함하여 질문 생성
        image_url = "https://test.com/img1.png"
        content_with_image = f'질문 내용 <img src="{image_url}">'

        question = create_question(
            author=self.user,
            category=self.category,
            validated_data={
                "title": "질문 제목",
                "content": content_with_image,
            },
        )

        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(QuestionImage.objects.count(), 1)
        self.assertEqual(question.title, "질문 제목")
        first_image = QuestionImage.objects.first()
        assert first_image is not None
        self.assertEqual(first_image.img_url, image_url)

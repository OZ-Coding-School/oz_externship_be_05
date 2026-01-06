from typing import Any

from django.test import TestCase, override_settings

from apps.qna.models import QuestionCategory, QuestionImage
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

        self.valid_s3_url = "https://test-bucket.s3.ap-northeast-2.amazonaws.com/question_images/test.jpg"

    @override_settings(AWS_S3_BUCKET_NAME="test-bucket")
    def test_create_question_success(self) -> None:
        # HTML <img> 태그(http 기준) 사용
        content = f'이미지 포함 질문 <img src="{self.valid_s3_url}">'

        data: dict[str, Any] = {
            "title": "Test Question",
            "content": content,
        }

        create_question(author=self.user, category=self.category, validated_data=data)

        # 1개가 정상적으로 생성되어야 함
        self.assertEqual(QuestionImage.objects.count(), 1)

        # DB에는 Key만 저장되어야 함
        image = QuestionImage.objects.first()
        self.assertIsNotNone(image)
        if image:
            self.assertEqual(image.img_url, "question_images/test.jpg")

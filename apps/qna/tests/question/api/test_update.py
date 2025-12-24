from typing import Any, cast

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
        self.image1 = QuestionImage.objects.create(
            question=self.question,
            img_url="https://img.com/1.png",
        )
        self.image2 = QuestionImage.objects.create(
            question=self.question,
            img_url="https://img.com/2.png",
        )
        self.image3 = QuestionImage.objects.create(
            question=self.question,
            img_url="https://img.com/3.png",
        )

        self.url = reverse("question_detail", args=[self.question.id])

    # 200: 부분 수정
    def test_partial_update_title(self) -> None:
        response = self.client.patch(
            self.url,
            {"title": "수정된 제목"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = cast(dict[str, Any], response.data)
        self.assertEqual(data["title"], "수정된 제목")

    # 200: 이미지 1개 삭제 1개 등록
    def test_update_image_delete_and_add(self) -> None:
        image = QuestionImage.objects.create(
            question=self.question,
            img_url="https://old.com/1.png",
        )

        response = self.client.patch(
            self.url,
            {
                "images": {
                    "delete_ids": [image.id],
                    "add_urls": ["https://new.com/2.png"],
                }
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = cast(dict[str, Any], response.data)
        images = cast(list[dict[str, Any]], data["images"])
        urls = [img["img_url"] for img in images]

        self.assertIn("https://new.com/2.png", urls)

    # 200: 이미지 3개 중 1개 삭제 2개 유지
    def test_delete_one_image_out_of_three(self) -> None:
        response = self.client.patch(
            self.url,
            {
                "images": {
                    "delete_ids": [self.image2.id],
                }
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = cast(dict[str, Any], response.data)
        images = cast(list[dict[str, Any]], data["images"])

        # 응답 기준 검증
        returned_ids = {img["id"] for img in images}

        self.assertNotIn(self.image2.id, returned_ids)
        self.assertIn(self.image1.id, returned_ids)
        self.assertIn(self.image3.id, returned_ids)

        # DB 기준 검증
        remaining_ids = set(QuestionImage.objects.filter(question=self.question).values_list("id", flat=True))

        self.assertEqual(remaining_ids, {self.image1.id, self.image3.id})

    # 200: 이미지 전부 삭제 이미지 1개 등록
    def test_delete_all_images_and_add_one(self) -> None:
        response = self.client.patch(
            self.url,
            {
                "images": {
                    "delete_ids": [
                        self.image1.id,
                        self.image2.id,
                        self.image3.id,
                    ],
                    "add_urls": ["https://img.com/new.png"],
                }
            },
            format="json",
        )

        # 상태 코드 검증
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 검증
        data = cast(dict[str, Any], response.data)
        images = cast(list[dict[str, Any]], data["images"])

        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["img_url"], "https://img.com/new.png")

        # DB 검증
        remaining_images = QuestionImage.objects.filter(question=self.question)
        self.assertEqual(remaining_images.count(), 1)

        remaining_image = remaining_images.first()
        assert remaining_image is not None  # mypy

        self.assertEqual(
            remaining_image.img_url,
            "https://img.com/new.png",
        )

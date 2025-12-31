from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.user.models.user import RoleChoices, User


class PresignedUrlAPITests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("question_presigned_url")
        self.user = User.objects.create_user(
            email="test@test.com",
            password="test1234",
            name="유저",
            role=RoleChoices.ST,
            birthday="2000-01-01",
            gender="M",
            phone_number="010-0000-0000",
        )

    def test_presigned_url_unauthenticated_fail(self) -> None:
        """로그인하지 않은 사용자는 요청 불가"""
        response = self.client.post(self.url, {"file_name": "test.jpg"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_presigned_url_invalid_extension_fail(self) -> None:
        """허용되지 않은 확장자(.exe) 요청 시 400 에러"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"file_name": "virus.exe"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

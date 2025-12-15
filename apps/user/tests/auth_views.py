from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user.models.user import GenderChoices
from apps.user.views.auth import RefreshAPIView


class RefreshAPIViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            email="refresh@example.com",
            password="OldPass123!",
            name="Tester",
            birthday=date(2000, 1, 1),
            gender=GenderChoices.MALE,
            phone_number="01077778888",
        )

    def test_refresh_returns_new_access(self) -> None:
        refresh = RefreshToken.for_user(self.user)
        payload = {"refresh_token": str(refresh)}
        request = self.factory.post("/api/v1/accounts/refresh", payload, format="json")

        response = RefreshAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["refresh_token"], str(refresh))
        self.assertIn("access_token", response.data)

    def test_refresh_rejects_invalid_token(self) -> None:
        payload = {"refresh_token": "invalid.token.value"}
        request = self.factory.post("/api/v1/accounts/refresh", payload, format="json")

        response = RefreshAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

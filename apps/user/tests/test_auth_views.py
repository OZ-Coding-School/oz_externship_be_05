from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apps.user.views.auth import LoginAPIView, SignupAPIView


class SignupAPIViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @patch("apps.user.views.auth.SignupSerializer")
    def test_signup_success_returns_201(self, serializer_mock: Any) -> None:
        serializer = MagicMock()
        serializer.is_valid.return_value = None
        serializer.save.return_value = None
        serializer_mock.return_value = serializer

        request = self.factory.post("/api/v1/accounts/signup", {"any": "data"}, format="json")

        response = SignupAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        serializer.is_valid.assert_called_once_with(raise_exception=True)
        serializer.save.assert_called_once()

    @patch("apps.user.views.auth.SignupSerializer")
    def test_signup_invalid_returns_400(self, serializer_mock: Any) -> None:
        serializer = MagicMock()
        serializer.is_valid.side_effect = ValidationError("bad")
        serializer_mock.return_value = serializer

        request = self.factory.post("/api/v1/accounts/signup", {"any": "data"}, format="json")

        response = SignupAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginAPIViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            email="login@example.com",
            password="Pass1234!",
            name="Tester",
            birthday=date(2000, 1, 1),
            gender="M",
            phone_number="01012345678",
        )

    @patch("apps.user.views.auth.issue_token_pair", return_value={"refresh_token": "r", "access_token": "a"})
    @patch("apps.user.views.auth.LoginSerializer")
    def test_login_success_returns_tokens(self, serializer_mock: Any, _token_mock: Any) -> None:
        serializer = MagicMock()
        serializer.is_valid.return_value = None
        serializer.validated_data = {"user": self.user}
        serializer_mock.return_value = serializer

        request = self.factory.post("/api/v1/accounts/login", {"email": "x", "password": "y"}, format="json")

        response = LoginAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["refresh_token"], "r")
        self.assertEqual(response.data["access_token"], "a")

    @patch("apps.user.views.auth.LoginSerializer")
    def test_login_invalid_returns_400(self, serializer_mock: Any) -> None:
        serializer = MagicMock()
        serializer.is_valid.side_effect = ValidationError("bad")
        serializer_mock.return_value = serializer

        request = self.factory.post("/api/v1/accounts/login", {"email": "x", "password": "y"}, format="json")

        response = LoginAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

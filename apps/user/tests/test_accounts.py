from __future__ import annotations

import base64
from datetime import date, timedelta
from typing import Any
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.user.models import Withdrawal, WithdrawalReason
from apps.user.models.user import GenderChoices
from apps.user.views.account import (
    ChangePasswordAPIView,
    ChangePhoneAPIView,
    CheckNicknameAPIView,
    MeAPIView,
)


class MeAPIViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            email="me@example.com",
            password="OldPass123!",
            name="Tester",
            birthday=date(2000, 1, 1),
            gender=GenderChoices.MALE,
            phone_number="01011112222",
        )

    def test_me_get_returns_profile(self) -> None:
        request = self.factory.get("/api/v1/accounts/me")
        force_authenticate(request, user=self.user)

        response = MeAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "me@example.com")

    def test_me_patch_updates_profile(self) -> None:
        payload = {"nickname": "newnick", "name": "New Name"}
        request = self.factory.patch("/api/v1/accounts/me", payload, format="json")
        force_authenticate(request, user=self.user)

        response = MeAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, "newnick")
        self.assertEqual(self.user.name, "New Name")

    @override_settings(WITHDRAWAL_GRACE_DAYS=7)
    def test_me_delete_creates_withdrawal_and_deactivates(self) -> None:
        payload = {"reason": WithdrawalReason.GRADUATION, "reason_detail": "done"}
        request = self.factory.delete("/api/v1/accounts/me", payload, format="json")
        force_authenticate(request, user=self.user)

        response = MeAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        withdrawal = Withdrawal.objects.get(user=self.user)
        expected_due_date = timezone.now().date() + timedelta(days=7)
        self.assertEqual(withdrawal.due_date, expected_due_date)

    def test_me_delete_defaults_reason_and_detail(self) -> None:
        request = self.factory.delete("/api/v1/accounts/me", {}, format="json")
        force_authenticate(request, user=self.user)

        response = MeAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        withdrawal = Withdrawal.objects.get(user=self.user)
        self.assertEqual(withdrawal.reason, WithdrawalReason.OTHER)
        self.assertEqual(withdrawal.reason_detail, "")


class CheckNicknameAPIViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    def test_check_nickname_conflict(self) -> None:
        get_user_model().objects.create_user(
            email="dup@example.com",
            password="OldPass123!",
            name="Tester",
            birthday=date(2000, 1, 1),
            gender=GenderChoices.MALE,
            phone_number="01022223333",
            nickname="tester",
        )
        request = self.factory.post("/api/v1/accounts/check-nickname", {"nickname": "Tester"}, format="json")

        response = CheckNicknameAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_check_nickname_available(self) -> None:
        request = self.factory.post("/api/v1/accounts/check-nickname", {"nickname": "free"}, format="json")

        response = CheckNicknameAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ChangePasswordAPIViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            email="pw@example.com",
            password="OldPass123!",
            name="Tester",
            birthday=date(2000, 1, 1),
            gender=GenderChoices.MALE,
            phone_number="01033334444",
        )

    def test_change_password_success(self) -> None:
        payload = {"current_password": "OldPass123!", "new_password": "NewPass123!"}
        request = self.factory.patch("/api/v1/accounts/change-password", payload, format="json")
        force_authenticate(request, user=self.user)

        response = ChangePasswordAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass123!"))

    def test_change_password_rejects_wrong_current(self) -> None:
        payload = {"current_password": "WrongPass123!", "new_password": "NewPass123!"}
        request = self.factory.patch("/api/v1/accounts/change-password", payload, format="json")
        force_authenticate(request, user=self.user)

        response = ChangePasswordAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChangePhoneAPIViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            email="phone@example.com",
            password="OldPass123!",
            name="Tester",
            birthday=date(2000, 1, 1),
            gender=GenderChoices.MALE,
            phone_number="01055556666",
        )

    @patch("apps.user.serializers.mixins.SMSSender.verify_token", return_value="01099998888")
    def test_change_phone_updates_number(self, verify_mock: Any) -> None:
        token = base64.urlsafe_b64encode(b"a" * settings.VERIFICATION_TOKEN_BYTES).rstrip(b"=").decode()
        payload = {"sms_token": token}
        request = self.factory.patch("/api/v1/accounts/change-phone", payload, format="json")
        force_authenticate(request, user=self.user)

        response = ChangePhoneAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, "01099998888")

    @patch("apps.user.serializers.mixins.SMSSender.verify_token", return_value="01077778888")
    def test_change_phone_rejects_duplicate(self, verify_mock: Any) -> None:
        get_user_model().objects.create_user(
            email="dup-phone@example.com",
            password="OldPass123!",
            name="Tester",
            birthday=date(2000, 1, 1),
            gender=GenderChoices.MALE,
            phone_number="01077778888",
        )
        token = base64.urlsafe_b64encode(b"a" * settings.VERIFICATION_TOKEN_BYTES).rstrip(b"=").decode()
        payload = {"sms_token": token}
        request = self.factory.patch("/api/v1/accounts/change-phone", payload, format="json")
        force_authenticate(request, user=self.user)

        response = ChangePhoneAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

import base64
from datetime import date
from typing import Any
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.user.models import Withdrawal
from apps.user.models.user import GenderChoices, User
from apps.user.utils.sender import EmailSender
from apps.user.views.recovery import (
    FindEmailAPIView,
    FindPasswordAPIView,
    RestoreAccountAPIView,
)


def make_token() -> str:
    token_bytes = getattr(settings, "VERIFICATION_TOKEN_BYTES", 32)
    return base64.urlsafe_b64encode(b"a" * token_bytes).rstrip(b"=").decode()


class RecoveryAPIViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @patch("apps.user.serializers.mixins.EmailSender.verify_token", return_value="restore@test.com")
    def test_restore_account_clears_withdrawal_and_activates(self, _verify_mock: Any) -> None:
        user = get_user_model().objects.create_user(
            email="restore@test.com",
            password="Super123@!",
            name="후회가많은사람",
            birthday=date(2007, 8, 1),
            gender=GenderChoices.MALE,
            phone_number="01012345678",
        )
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        Withdrawal.objects.create(user=user, reason="OTHER", reason_detail="노잼", due_date=date.today())

        request = self.factory.patch(
            "/api/v1/accounts/restore",
            {"email_token": make_token()},
            format="json",
        )
        response = RestoreAccountAPIView.as_view()(request)

        user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.is_active)
        self.assertFalse(Withdrawal.objects.filter(user=user).exists())

    @patch("apps.user.serializers.mixins.SMSSender.verify_token", return_value="01012345679")
    def test_find_email_returns_masked_email(self, _verify_mock: Any) -> None:
        user = User.objects.create_user(
            email="bbibbi@example.com",
            password="Idiot123!",
            name="지이메일까먹는삣삐",
            birthday=date(2007, 8, 1),
            gender=GenderChoices.FEMALE,
            phone_number="01012345679",
        )

        request = self.factory.post(
            "/api/v1/accounts/find-email",
            {"name": user.name, "sms_token": make_token()},
            format="json",
        )
        response = FindEmailAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["masked_email"], EmailSender.mask_email("bbibbi@example.com"))

    @patch("apps.user.serializers.mixins.EmailSender.verify_token", return_value="pw@test.com")
    def test_find_password_updates_password(self, _verify_mock: Any) -> None:
        user = get_user_model().objects.create_user(
            email="pw@test.com",
            password="OldPass123!",
            name="지비번까먹는삣삐",
            birthday=date(2000, 1, 1),
            gender=GenderChoices.MALE,
            phone_number="01039393939",
        )

        request = self.factory.post(
            "/api/v1/accounts/find-password",
            {"email_token": make_token(), "new_password": "NewStrongPass123!"},
            format="json",
        )
        response = FindPasswordAPIView.as_view()(request)

        user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.check_password("NewStrongPass123!"))

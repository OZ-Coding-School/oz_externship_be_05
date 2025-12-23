import base64
from datetime import date
from typing import Any, cast
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apps.user.models.user import GenderChoices
from apps.user.serializers.auth import SignupSerializer
from apps.user.serializers.base import BaseMixin
from apps.user.serializers.mixins import SenderMixin
from apps.user.serializers.social_profile import KakaoProfileSerializer
from apps.user.serializers.verification import SignupEmailRequestSerializer
from apps.user.utils.sender import EmailSender, SMSSender
from apps.user.utils.verification import VerificationService
from apps.user.validaters.validate_token import is_valid_token_format
from apps.user.views.verification import (
    SendEmailAPIView,
    SendSMSVerificationAPIView,
    VerifyEmailAPIView,
    VerifySMSAPIView,
)


class BaseMixinValidationTests(TestCase):
    def setUp(self) -> None:
        class Dummy(BaseMixin):
            pass

        self.dummy = Dummy()

    def test_verify_code_validation(self) -> None:
        with self.assertRaises(serializers.ValidationError):
            self.dummy.validate_verify_code("12")
        with self.assertRaises(serializers.ValidationError):
            self.dummy.validate_verify_code("ABCDEF")
        self.assertEqual(self.dummy.validate_verify_code("123456"), "123456")

    def test_verify_token_validation(self) -> None:
        valid_token = base64.urlsafe_b64encode(b"x" * 32).rstrip(b"=").decode()
        self.assertTrue(is_valid_token_format(valid_token, token_bytes=32))
        self.assertEqual(self.dummy.validate_verify_token(valid_token), valid_token)
        with self.assertRaises(serializers.ValidationError):
            self.dummy.validate_verify_token("invalid*token")


class SenderMixinTests(TestCase):
    def test_verify_sms_token_uses_sender_class(self) -> None:
        class StubSmsSender:
            def verify_token(self, token: str) -> str:
                return "01099998888"

        class Dummy(SenderMixin):
            sms_sender_class = cast(type[SMSSender], StubSmsSender)

        self.assertEqual(Dummy().verify_sms_token("token"), "01099998888")

    def test_verify_email_token_bubbles_validation_error(self) -> None:
        class StubEmailSender:
            def verify_token(self, token: str) -> str:
                raise ValidationError("bad token")

        class Dummy(SenderMixin):
            email_sender_class = cast(type[EmailSender], StubEmailSender)

        with self.assertRaises(ValidationError):
            Dummy().verify_email_token("token")


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class VerificationServiceTests(TestCase):
    def setUp(self) -> None:
        self.service = VerificationService(code_length=4, token_bytes=4)

    def test_generate_and_verify_code_consumes(self) -> None:
        code = self.service.generate_code("User@Example.com")
        self.assertEqual(len(code), 4)
        self.assertFalse(self.service.verify("user@example.com", "9999"))
        self.assertTrue(self.service.verify("user@example.com", code))
        self.assertFalse(self.service.verify("user@example.com", code))

    def test_generate_and_verify_token_lookup(self) -> None:
        token = self.service.generate_token("MiXeD@Email.Com")
        identifier = self.service.verify_token(token, consume=False)
        self.assertEqual(identifier, "mixed@email.com")
        self.assertEqual(self.service.verify("mixed@email.com", token, is_token=True), True)
        self.assertIsNone(self.service.verify_token(token, consume=True))

    def test_delete_token_and_get_ttl(self) -> None:
        token = self.service.generate_token("delete_me@example.com")
        self.service.delete(token, is_token=True)
        self.assertIsNone(self.service.verify_token(token, consume=False))
        self.assertIsNone(self.service.get_remaining_ttl("anything", is_token=True))


class SignupSerializerTests(TestCase):
    @patch("apps.user.serializers.mixins.SMSSender.verify_token", return_value="01011112222")
    @patch("apps.user.serializers.mixins.EmailSender.verify_token", return_value="signup@example.com")
    def test_signup_serializer_creates_user(self, email_mock: Any, sms_mock: Any) -> None:
        token = base64.urlsafe_b64encode(b"a" * 32).rstrip(b"=").decode()
        data = {
            "password": "StrongPass123!",
            "name": "Tester",
            "birthday": date(2000, 1, 1),
            "gender": GenderChoices.MALE,
            "nickname": "tester",
            "sms_token": token,
            "email_token": token,
        }
        serializer = SignupSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.email, "signup@example.com")
        self.assertEqual(user.phone_number, "01011112222")
        self.assertEqual(user.name, "Tester")

    @patch("apps.user.serializers.mixins.SMSSender.verify_token", return_value="01022223333")
    @patch("apps.user.serializers.mixins.EmailSender.verify_token", return_value="dup@example.com")
    def test_signup_serializer_rejects_duplicates(self, email_mock: Any, sms_mock: Any) -> None:
        get_user_model().objects.create_user(
            email="dup@example.com",
            password="pw123456!",
            name="Existing",
            birthday=date(2000, 1, 1),
            gender=GenderChoices.MALE,
            phone_number="01022223333",
        )
        token = base64.urlsafe_b64encode(b"b" * 32).rstrip(b"=").decode()
        data = {
            "password": "StrongPass123!",
            "name": "Tester",
            "birthday": date(2000, 1, 1),
            "gender": GenderChoices.MALE,
            "sms_token": token,
            "email_token": token,
        }
        serializer = SignupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_signup_serializer_requires_tokens(self) -> None:
        data = {
            "password": "StrongPass123!",
            "name": "Tester",
            "birthday": "2000-01-01",
            "gender": GenderChoices.MALE,
        }
        serializer = SignupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("sms_token", serializer.errors)
        self.assertIn("email_token", serializer.errors)


class SocialProfileSerializerTests(TestCase):
    def test_kakao_serializer_requires_nickname_and_email(self) -> None:
        serializer = KakaoProfileSerializer(data={"id": "1", "kakao_account": {"profile": {}, "email": "a@a.com"}})
        self.assertFalse(serializer.is_valid())
        serializer = KakaoProfileSerializer(data={"id": "1", "kakao_account": {"profile": {"nickname": "hi"}}})
        self.assertFalse(serializer.is_valid())


class VerificationSerializersTests(TestCase):
    def test_signup_email_request_blocks_existing(self) -> None:
        get_user_model().objects.create_user(
            email="exists@example.com",
            password="pw123456!",
            name="Existing",
            birthday=date(2000, 1, 1),
            gender=GenderChoices.FEMALE,
            phone_number="01000000000",
        )
        serializer = SignupEmailRequestSerializer(data={"email": "exists@example.com"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


class VerificationAPIViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @patch("apps.user.views.verification.EmailSender.send")
    def test_send_email_calls_sender(self, send_mock: Any) -> None:
        request = self.factory.post("/api/v1/accounts/verification/send-email", {"email": "a@test.com"}, format="json")

        response = SendEmailAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        send_mock.assert_called_once_with("a@test.com")

    @patch("apps.user.views.verification.EmailSender.verify_code", return_value="token")
    def test_verify_email_success_returns_token(self, verify_mock: Any) -> None:
        payload = {"email": "a@test.com", "email_code": "123456"}
        request = self.factory.post("/api/v1/accounts/verification/verify-email", payload, format="json")

        response = VerifyEmailAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email_token"], "token")
        verify_mock.assert_called_once_with("a@test.com", "123456")

    @patch("apps.user.views.verification.EmailSender.verify_code", side_effect=ValidationError("bad"))
    def test_verify_email_invalid_returns_400(self, _verify_mock: Any) -> None:
        payload = {"email": "a@test.com", "email_code": "123456"}
        request = self.factory.post("/api/v1/accounts/verification/verify-email", payload, format="json")

        response = VerifyEmailAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.user.views.verification.SMSSender.send")
    def test_send_sms_calls_sender(self, send_mock: Any) -> None:
        request = self.factory.post(
            "/api/v1/accounts/verification/send-sms", {"phone_number": "01012345678"}, format="json"
        )

        response = SendSMSVerificationAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        send_mock.assert_called_once_with("01012345678")

    @patch("apps.user.views.verification.SMSSender.verify_code", return_value="token")
    def test_verify_sms_success_returns_token(self, verify_mock: Any) -> None:
        payload = {"phone_number": "01012345678", "sms_code": "123456"}
        request = self.factory.post("/api/v1/accounts/verification/verify-sms", payload, format="json")

        response = VerifySMSAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sms_token"], "token")
        verify_mock.assert_called_once_with("01012345678", "123456")

    @patch("apps.user.views.verification.SMSSender.verify_code", side_effect=ValidationError("bad"))
    def test_verify_sms_invalid_returns_400(self, _verify_mock: Any) -> None:
        payload = {"phone_number": "01012345678", "sms_code": "123456"}
        request = self.factory.post("/api/v1/accounts/verification/verify-sms", payload, format="json")

        response = VerifySMSAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

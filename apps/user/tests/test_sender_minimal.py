from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from rest_framework.exceptions import APIException, ValidationError

from apps.user.utils.sender import EmailSender, SMSSender


class SenderMinimalTests(TestCase):
    def test_sender_verify_token_ok_and_expired(self) -> None:
        vs = MagicMock()
        vs.verify_token.return_value = "a@test.com"
        sender = EmailSender(verification_service=vs)
        self.assertEqual(sender.verify_token("tok"), "a@test.com")

        vs.verify_token.return_value = None
        sender2 = EmailSender(verification_service=vs)
        with self.assertRaises(ValidationError):
            sender2.verify_token("tok")

    def test_email_mask_email_basic(self) -> None:
        self.assertEqual(EmailSender.mask_email("abcdef@gmail.com", 1, 1), "a****f@gmail.com")

    @override_settings(DEFAULT_FROM_EMAIL="noreply@test.com")
    @patch("apps.user.utils.sender.send_mail", autospec=True)
    def test_email_send_ok(self, send_mail_mock: MagicMock) -> None:
        vs = MagicMock()
        vs.generate_code.return_value = "123456"
        sender = EmailSender(verification_service=vs)
        sender.send("to@test.com")
        send_mail_mock.assert_called_once()

    @override_settings(DEFAULT_FROM_EMAIL="noreply@test.com")
    @patch("apps.user.utils.sender.send_mail", side_effect=Exception("fail"), autospec=True)
    def test_email_send_fail_raises(self, _send_mail_mock: MagicMock) -> None:
        vs = MagicMock()
        vs.generate_code.return_value = "123456"
        sender = EmailSender(verification_service=vs)
        with self.assertRaises(APIException):
            sender.send("to@test.com")

    @override_settings(TWILIO_ACCOUNT_SID=None, TWILIO_AUTH_TOKEN=None, TWILIO_VERIFY_SERVICE_SID=None)
    def test_sms_sender_init_missing_settings_raises(self) -> None:
        with self.assertRaises(APIException):
            SMSSender()

    def test_sms_make_it_korean(self) -> None:
        self.assertEqual(SMSSender.make_it_korean("010-1234-5678"), "+821012345678")

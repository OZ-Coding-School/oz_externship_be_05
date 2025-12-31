from __future__ import annotations

from django.http import HttpRequest
from django.test import TestCase

from apps.core.response import MagicException, ResponseMessage
from apps.core.response.response_message import resolve_message


class ResponseMessageTests(TestCase):
    def setUp(self) -> None:
        self.request = HttpRequest()
        self.request.META["HTTP_X_COUNTRY_CODE"] = "EN"

    def test_response_message_renders_template(self) -> None:
        resp = ResponseMessage(self.request, 200, "SMS_COOLDOWN", time=5)
        self.assertEqual(resp.data["detail"], "Please try again in 5 seconds.")

    def test_response_message_fallbacks_to_kr(self) -> None:
        request = HttpRequest()
        request.META["HTTP_X_COUNTRY_CODE"] = "JP"
        resp = ResponseMessage(request, 200, "SMS_COOLDOWN", time=5)
        self.assertEqual(resp.data["detail"], "5초 후에 다시 시도해주세요.")

    def test_resolve_message_fallbacks_to_kr(self) -> None:
        request = HttpRequest()
        request.META["HTTP_X_COUNTRY_CODE"] = "XX"
        message = resolve_message("SMS_COOLDOWN", request, {"time": 10})
        self.assertEqual(message, "10초 후에 다시 시도해주세요.")

    def test_magic_exception_fields(self) -> None:
        exc = MagicException(status_code=429, message_code="SMS_COOLDOWN", time=3)
        self.assertEqual(exc.status_code, 429)
        self.assertEqual(exc.message_code, "SMS_COOLDOWN")
        self.assertEqual(exc.variables["time"], 3)

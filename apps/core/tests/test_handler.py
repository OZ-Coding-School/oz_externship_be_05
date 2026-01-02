from typing import Any, cast
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.views import APIView

from apps.core.exceptions.exception_handler import custom_exception_handler
from apps.core.exceptions.exception_messages import EMS
from apps.core.response.response_message import MagicException


class ExceptionHandlerTestCase(TestCase):
    def setUp(self) -> None:
        """exception_handler 호출 시 전달될 request / view mock 구성"""
        self.request: MagicMock = MagicMock()
        # cast를 사용하여 mypy 경고 제거
        self.view: Any = cast(Any, APIView())
        self.context: dict[str, Any] = {"view": self.view, "request": self.request}

    @patch("apps.core.exceptions.exception_handler.logger")
    def test_unhandled_exception_returns_500_and_logs_error(self, mock_logger: MagicMock) -> None:
        """
        처리되지 않은 예외 발생 시
        - 상태코드 500 반환
        - EMS 정의된 기본 메시지 반환
        - logger.error 호출 및 exc_info 포함
        """
        exception: ZeroDivisionError = ZeroDivisionError("division by zero")

        response = custom_exception_handler(exception, self.context)

        assert response is not None
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, EMS.E500_INTERNAL_ERROR)

        # logger 호출 확인
        mock_logger.error.assert_called_once()
        _, kwargs = mock_logger.error.call_args
        self.assertTrue(kwargs.get("exc_info"))

    @patch("apps.core.exceptions.exception_handler.resolve_message")
    def test_magic_exception_is_resolved_and_formatted(self, mock_resolve: MagicMock) -> None:
        """
        MagicException 발생 시
        - resolve_message를 통해 메시지 해석
        - 상태코드와 해석된 메시지 반환
        """
        exception: MagicException = MagicException(
            message_code="MSG_001",
            status_code=400,
            variables={"name": "test"},
        )
        mock_resolve.return_value = "해석된 메시지입니다."

        response = custom_exception_handler(exception, self.context)

        assert response is not None
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "해석된 메시지입니다.")

    def test_validation_error_uses_default_message(self) -> None:
        """
        ValidationError 발생 시
        - view에 커스텀 메시지가 없으면 기본 메시지 사용
        - errors 필드에 상세 에러 반환
        """
        exception: ValidationError = ValidationError({"email": ["이메일 형식이 아닙니다."]})

        response = custom_exception_handler(exception, self.context)

        assert response is not None
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "유효하지 않은 요청입니다.")
        self.assertEqual(response.data["errors"], {"email": ["이메일 형식이 아닙니다."]})

    def test_validation_error_uses_view_custom_message(self) -> None:
        """
        ValidationError 발생 시
        - view에 validation_error_message 정의되어 있으면 이를 사용
        """
        # cast로 mypy 경고 제거 후 속성 추가
        self.view.validation_error_message = "입력값이 잘못되었습니다!"
        exception: ValidationError = ValidationError({"field": ["error"]})

        response = custom_exception_handler(exception, self.context)

        assert response is not None
        self.assertEqual(response.data["error_detail"], "입력값이 잘못되었습니다!")

    def test_detail_key_is_renamed_to_error_detail(self) -> None:
        """
        NotFound 예외 발생 시
        - response.data['detail']을 'error_detail'로 rename
        - 상태코드 및 메시지 확인
        """
        exception: NotFound = NotFound("리소스를 찾을 수 없습니다.")

        response = custom_exception_handler(exception, self.context)

        assert response is not None
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "리소스를 찾을 수 없습니다.")

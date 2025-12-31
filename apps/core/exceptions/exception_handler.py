from typing import Any, Optional

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.core.response.response_message import MagicException, resolve_message


def custom_exception_handler(
    exc: Exception,
    context: dict[str, Any],
) -> Optional[Response]:
    response = exception_handler(exc, context)
    if response is None:
        return None

    view = context.get("view")
    request = context.get("request")

    if isinstance(exc, MagicException):
        message = resolve_message(exc.message_code, request, exc.variables)
        detail_key = "error_detail" if str(exc.status_code).startswith(("4", "5")) else "detail"
        return Response({detail_key: message}, status=exc.status_code)

    # 400 → validation_error_message / "유효하지 않은 요청입니다."
    if isinstance(exc, ValidationError):
        message = getattr(view, "validation_error_message", "유효하지 않은 요청입니다.")

        response.data = {
            "error_detail": message,
            "errors": exc.detail,
        }
        return response

    # 401 / 403 / 404 등 detail → error_detail
    if isinstance(response.data, dict) and "detail" in response.data:
        response.data = {"error_detail": str(response.data["detail"])}

    return response

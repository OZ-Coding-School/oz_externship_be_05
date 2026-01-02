import logging
from typing import Any, Optional

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.core.exceptions.exception_messages import EMS
from apps.core.response.response_message import MagicException, resolve_message

logger = logging.getLogger(__name__)


def custom_exception_handler(
    exc: Exception,
    context: dict[str, Any],
) -> Optional[Response]:
    response = exception_handler(exc, context)
    if response is None:
        logger.error(f"[System Error] {exc}", exc_info=True)
        return Response(EMS.E500_INTERNAL_ERROR, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

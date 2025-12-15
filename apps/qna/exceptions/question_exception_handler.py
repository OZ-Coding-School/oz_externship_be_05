from typing import Any, Optional

from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.qna.exceptions.question_exceptions import (
    QuestionCreateValidationError,
)

VALIDATION_ERRORS = (QuestionCreateValidationError,)


def custom_exception_handler(
    exc: Exception,
    context: dict[str, Any],
) -> Optional[Response]:
    response = exception_handler(exc, context)
    if response is None:
        return None

    # 400 ValidationError 계열
    if isinstance(exc, VALIDATION_ERRORS):
        detail = exc.detail

        # detail이 list인 경우 (ValidationError 기본 형태)
        if isinstance(detail, list) and detail:
            response.data = {"error_detail": str(detail[0])}
        # detail이 dict인 경우
        elif isinstance(detail, dict):
            response.data = {"error_detail": next(iter(detail.values()))}
        else:
            response.data = {"error_detail": str(detail)}

        return response

    # detail → error_detail 통일
    if isinstance(response.data, dict) and "detail" in response.data:
        response.data = {"error_detail": str(response.data["detail"])}

    return response

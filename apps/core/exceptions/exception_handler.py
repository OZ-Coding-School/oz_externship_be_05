from typing import Any, Optional

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.qna.views.question.question_create import QuestionCreateAPIView


def custom_exception_handler(
    exc: Exception,
    context: dict[str, Any],
) -> Optional[Response]:
    response = exception_handler(exc, context)
    if response is None:
        return None

    view = context.get("view")

    # 질문 등록 API 전용 400 메시지
    if isinstance(exc, ValidationError) and isinstance(view, QuestionCreateAPIView):
        response.data = {"error_detail": "유효하지 않은 질문 등록 요청입니다."}
        return response

    # 공통 ValidationError 포맷 통일
    if isinstance(exc, ValidationError):
        detail = exc.detail

        if isinstance(detail, list) and detail:
            response.data = {"error_detail": str(detail[0])}
        elif isinstance(detail, dict):
            response.data = {"error_detail": next(iter(detail.values()))}
        else:
            response.data = {"error_detail": str(detail)}

        return response

    # 401 / 403 / 404 등 detail → error_detail
    if isinstance(response.data, dict) and "detail" in response.data:
        response.data = {"error_detail": str(response.data["detail"])}

    return response

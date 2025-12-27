from rest_framework import status
from rest_framework.exceptions import APIException

from apps.core.exceptions.exception_messages import EMS


class ConflictException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "요청 처리 중 충돌이 발생했습니다."
    default_code = "conflict"

    def __init__(self, *, action: str | None = None, detail: str | None = None, code: str | None = None) -> None:
        if detail is not None:
            resolved_detail = detail
        elif action is not None:
            resolved_detail = EMS.E409_CONFLICT_ON_ACTION(action)["error_detail"]
        else:
            resolved_detail = self.default_detail

        super().__init__(
            detail=resolved_detail,
            code=code or self.default_code,
        )

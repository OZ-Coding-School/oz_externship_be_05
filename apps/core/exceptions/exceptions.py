from rest_framework import status
from rest_framework.exceptions import APIException


class LockedException(APIException):
    """
    423 Locked
    리소스가 잠겨있어 접근할 수 없을 때 사용
    """

    status_code = status.HTTP_423_LOCKED
    default_detail = "리소스가 잠겨있습니다."
    default_code = "locked"


class GoneException(APIException):
    """
    410 Gone: 요청한 리소스가 영구적으로 삭제되었거나 만료됨 (시험 종료 등)
    """

    status_code = status.HTTP_410_GONE
    default_detail = "요청한 리소스가 만료되었습니다."
    default_code = "gone"

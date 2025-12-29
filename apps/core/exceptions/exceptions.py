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

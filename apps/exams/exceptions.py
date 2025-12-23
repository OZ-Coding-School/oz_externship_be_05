from rest_framework import status
from rest_framework.exceptions import APIException


class DeploymentConflictException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "동일한 조건의 배포가 이미 존재합니다."
    default_code = "deployment_conflict"

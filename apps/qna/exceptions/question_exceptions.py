from rest_framework import status
from rest_framework.exceptions import APIException

from apps.core.exceptions.exception_messages import EMS


# 도메인 예외 정의
## 등록
class QuestionCreateNotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = EMS.E401_STUDENT_ONLY_ACTION("질문을 등록")["error_detail"]


## 상세조회
class QuestionNotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = EMS.E404_NOT_FOUND("해당 질문")["error_detail"]


## 수정
class QuestionUpdateNotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = EMS.E401_USER_ONLY_ACTION("질문을 수정")["error_detail"]

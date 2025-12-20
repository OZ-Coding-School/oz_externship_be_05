from rest_framework import status
from rest_framework.exceptions import APIException

from apps.core.exceptions.exception_messages import EMS


# 도메인 예외 정의
## 등록
class QuestionCreateNotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = EMS.E401_STUDENT_ONLY_ACTION("질문을 등록")["error_detail"]


class CategoryNotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = EMS.E404_NOT_FOUND("카테고리")["error_detail"]


## 조회
class QuestionListEmptyError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = EMS.E404_NO_QUESTIONS_AVAILABLE["error_detail"]


## 상세조회
class QuestionNotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = EMS.E404_NOT_FOUND("질문")["error_detail"]

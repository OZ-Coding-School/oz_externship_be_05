from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError


# ValidationError 400 처리
class QuestionCreateValidationError(ValidationError):
    default_detail = "유효하지 않은 질문 등록 요청입니다."


# 도메인 예외 정의
## 등록
class QuestionCreateNotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "로그인한 수강생만 질문을 등록할 수 있습니다."


class CategoryNotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "선택한 카테고리를 찾을 수 없습니다."


class DuplicateQuestionTitleError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "중복된 질문 제목이 이미 존재합니다."

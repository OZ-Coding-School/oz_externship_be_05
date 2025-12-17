from rest_framework import status
from rest_framework.exceptions import APIException


# 도메인 예외 정의
## 등록
class QuestionCreateNotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "로그인한 수강생만 질문을 등록할 수 있습니다."


class CategoryNotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "선택한 카테고리를 찾을 수 없습니다."


## 조회
class QuestionListEmptyError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "조회 가능한 질문이 존재하지 않습니다."

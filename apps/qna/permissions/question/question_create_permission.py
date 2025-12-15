from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.qna.exceptions.question_exceptions import QuestionCreateNotAuthenticated
from apps.user.models.user import RoleChoices


class QuestionCreatePermission(BasePermission):
    message = "질문 등록 권한이 없습니다."  # 403

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user

        # 401: 인증 안됨 → 커스텀 예외
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            raise QuestionCreateNotAuthenticated()

        # 403: 인증은 됐지만 학생 아님
        return user.role == RoleChoices.ST

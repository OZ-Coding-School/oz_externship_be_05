from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.core.exceptions.exception_messages import EMS
from apps.qna.exceptions.question_exceptions import QuestionCreateNotAuthenticated
from apps.user.models.user import RoleChoices


class QuestionCreatePermission(BasePermission):
    message = EMS.E403_QNA_PERMISSION_DENIED("등록")["error_detail"]

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user

        # 401: 인증 안됨 → 커스텀 예외
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            raise QuestionCreateNotAuthenticated()

        # 403: 인증은 됐지만 학생 아님
        if user.role != RoleChoices.ST:
            return False

        return True

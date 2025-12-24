from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.core.exceptions.exception_messages import EMS
from apps.qna.exceptions.question_exceptions import QuestionUpdateNotAuthenticated
from apps.qna.models import Question
from apps.user.models.user import RoleChoices
from rest_framework.exceptions import PermissionDenied

class QuestionUpdatePermission(BasePermission):

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user

        # 401
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            raise QuestionUpdateNotAuthenticated()

        # 학생만 가능
        if request.user.role != RoleChoices.ST:
            raise PermissionDenied(
                detail=EMS.E403_QNA_PERMISSION_DENIED("등록")["error_detail"]
            )

        return True

    # 작성자 본인만 가능
    def has_object_permission(self, request: Request, view: APIView, obj: Question) -> bool:
        if obj.author_id != request.user.id:
            raise PermissionDenied(
                detail=EMS.E403_OWNER_ONLY_EDIT("질문")["error_detail"]
            )
        return True

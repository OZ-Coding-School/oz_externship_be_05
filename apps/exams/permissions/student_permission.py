from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models.exam_submission import ExamSubmission
from apps.user.models.user import RoleChoices


class IsSubmissionOwner(BasePermission):
    """
    ExamSubmission의 submitter 본인만 접근 가능
    """

    message = EMS.E403_QUIZ_PERMISSION_DENIED("조회")

    def has_object_permission(
        self,
        request: Request,
        view: APIView,
        obj: ExamSubmission,
    ) -> bool:
        return obj.submitter_id == request.user.id


class IsStudentRole(BasePermission):
    """
    학생 권한 확인 Permission (Role 기반)
    """

    message = EMS.E403_QUIZ_PERMISSION_DENIED("학생")

    def has_permission(self, request: Request, view: APIView) -> bool:
        # role 기반 학생 판별
        role = getattr(request.user, "role", None)
        return role == RoleChoices.ST


class StudentUserPermissionView(APIView):
    """
    모든 학생 전용 view단이 상속받을 기본 클래스
    - JWT 인증 필수 401
    - 인증 안 됨 401
    - 학생(role 기반) 권한 필수
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsStudentRole]

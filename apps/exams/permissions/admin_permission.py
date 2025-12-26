from rest_framework.permissions import BasePermission, IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.core.exceptions.exception_messages import EMS
from apps.user.models.user import RoleChoices


class IsStaffOrAdmin(BasePermission):
    """
    관리자 권한 확인 Permission
    """

    message = EMS.E403_QUIZ_PERMISSION_DENIED("관리자")

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user

        # 슈퍼유저는 항상 허용
        if user.is_superuser:
            return True

        # role 기반 관리자 판별
        role = getattr(user, "role", None)

        return role in {RoleChoices.TA, RoleChoices.LC, RoleChoices.OM, RoleChoices.AD}


class AdminUserPermissionView(APIView):
    """
    모든 관리자 전용 view단이 상속받을 기본 클래스
    - JWT 인증 필수 401
    - 인증 안 됨 401
    - 관리자(role 기반) 권한 필수 403
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

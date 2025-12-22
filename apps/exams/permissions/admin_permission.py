from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.user.models.user import RoleChoices


class IsStaffOrAdmin(BasePermission):
    """
    관리자 권한 확인 Permission

    - 인증되지 않은 사용자 → 401
    - 관리자 권한 없는 사용자 → 403
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user

        # 인증 여부 확인 (401)
        if not user or not user.is_authenticated:
            return False

        # 슈퍼유저는 항상 허용
        if user.is_superuser:
            return True

        # role 기반 관리자 판별
        role = getattr(user, "role", None)

        return role in {RoleChoices.TA, RoleChoices.LC, RoleChoices.OM, RoleChoices.AD}


class AdminUserPermission(APIView):
    """
    모든 관리자 전용 view단이 상속받을 기본 클래스
    - IsAdminUser 권한을 적용합니다.
    """

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsStaffOrAdmin]  # AllowAny: 개발환경 테스트용

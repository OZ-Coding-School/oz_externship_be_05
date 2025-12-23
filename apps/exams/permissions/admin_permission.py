from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.user.models.user import RoleChoices


class IsStaffOrAdmin(BasePermission):
    """
    관리자 권한 확인 Permission

    - 인증 여부는 IsAuthenticated에서 처리
    - 관리자 권한 없는 사용자 → 403
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user

        # 슈퍼유저는 항상 허용
        if user.is_superuser:
            return True

        # role 기반 관리자 판별
        role = getattr(user, "role", None)

        return role in {RoleChoices.TA, RoleChoices.LC, RoleChoices.OM, RoleChoices.AD}


class AdminUserPermission(APIView):
    """
    모든 관리자 전용 view단이 상속받을 기본 클래스
    - JWT 인증 필수
    - 관리자(role 기반) 권한 필수
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

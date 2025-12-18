from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.views import APIView


class AdminUserPermission(APIView):
    """
    모든 관리자 전용 view단이 상속받을 기본 클래스
    - IsAdminUser 권한을 적용합니다.
    """

    permission_classes = [AllowAny]  # AllowAny: 개발환경 테스트용

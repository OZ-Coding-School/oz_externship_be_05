from rest_framework import pagination, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser


class CustomPageNumberPagination(pagination.PageNumberPagination):
    """
    관리자 API에서 사용할 공통 페이징 설정
    - 페이지 번호 기반 (page)
    - 페이지 크기 파라미터 이름: size
    - 기본 페이지 크기: 10
    - 최대 페이지 크기: 100
    """

    page_size_query_param = "size"
    page_size = 10
    max_page_size = 100


class AdminModelViewSet(viewsets.ModelViewSet):
    """
    모든 관리자 전용 CRUD ViewSet이 상속받을 기본 클래스
    - IsAdminUser 권한을 적용합니다.
    """

    permission_classes = [IsAdminUser]  # AllowAny: 개발환경 테스트용
    pagination_class = CustomPageNumberPagination

    valid_sort_fields = ["title", "created_at", "updated_at"]  # abc, 최신

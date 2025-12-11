from django.urls import URLPattern, URLResolver
from rest_framework.routers import DefaultRouter

from apps.exams.views.admin import ExamAdminViewSet

router = DefaultRouter()  # CRUD에 필요한 모든 URL 패턴을 자동으로 생성

# /api/v1/admin/exams 경로에 ExamAdminViewSet을 연결합니다.
router.register(r"", ExamAdminViewSet, basename="exam")

urlpatterns: list[URLPattern | URLResolver] = router.urls

from django.urls import URLPattern, URLResolver, path

from apps.exams.views.admin import (
    ExamAdminListCreateAPIView,
    ExamAdminRetrieveUpdateDestroyAPIView,
)

urlpatterns: list[URLPattern | URLResolver] = [
    # /api/v1/admin/exams/ 경로에 ExamAdminViewSet을 연결합니다.
    path("", ExamAdminListCreateAPIView.as_view(), name="exam"),
    path("<str:pk>/", ExamAdminRetrieveUpdateDestroyAPIView.as_view(), name="exam-detail"),
]

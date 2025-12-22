from django.urls import URLPattern, URLResolver, path

from apps.exams.views.admin import (
    ExamAdminListCreateAPIView,
    ExamAdminRetrieveUpdateDestroyAPIView,
)
from apps.exams.views.admin.admin_submission_view import AdminSubmissionListAPIView

urlpatterns: list[URLPattern | URLResolver] = [
    # submissions
    path("submissions/", AdminSubmissionListAPIView.as_view(), name="exam-submission"),
    # /api/v1/admin/exams/ 경로에 ExamAdminViewSet을 연결합니다.
    path("", ExamAdminListCreateAPIView.as_view(), name="exam"),
    path("<str:pk>/", ExamAdminRetrieveUpdateDestroyAPIView.as_view(), name="exam-detail"),
]

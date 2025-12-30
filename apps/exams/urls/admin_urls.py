from django.urls import URLPattern, URLResolver, path

from apps.exams.views.admin import (
    AdminDeploymentDetailUpdateDeleteView,
    DeploymentListCreateAPIView,
    ExamAdminListCreateAPIView,
    ExamAdminRetrieveUpdateDestroyAPIView,
    ExamDeploymentStatusAPIView,
)
from apps.exams.views.admin.admin_submission_view import AdminSubmissionListAPIView

urlpatterns: list[URLPattern | URLResolver] = [
    # /api/v1/admin/ 경로에 ExamAdminViewSet을 연결합니다.
    path("exams", ExamAdminListCreateAPIView.as_view(), name="exam"),
    path("exams/deployments", DeploymentListCreateAPIView.as_view(), name="exam-deployments"),
    path("exam/submissions", AdminSubmissionListAPIView.as_view(), name="exam-submission"),
    path(
        "exams/deployments/<int:deployment_id>",
        AdminDeploymentDetailUpdateDeleteView.as_view(),
        name="exam-deployment-detail",
    ),
    path(
        "exams/deployments/<int:deployment_id>/status",
        ExamDeploymentStatusAPIView.as_view(),
        name="exam-deployment-status",
    ),
    path("exams/<str:pk>", ExamAdminRetrieveUpdateDestroyAPIView.as_view(), name="exam-detail"),
]

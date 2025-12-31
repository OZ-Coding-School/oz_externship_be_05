from django.urls import URLPattern, URLResolver, path

from apps.exams.views.admin import (
    AdminDeploymentDetailUpdateDeleteView,
    DeploymentListCreateAPIView,
    ExamAdminListCreateAPIView,
    ExamAdminQuestionCreateAPIView,
    ExamAdminQuestionUpdateDestroyAPIView,
    ExamAdminRetrieveUpdateDestroyAPIView,
    ExamAdminSubmissionDetailView,
    ExamDeploymentStatusAPIView,
)
from apps.exams.views.admin.admin_submission_view import AdminSubmissionListAPIView

urlpatterns: list[URLPattern | URLResolver] = [
    # /api/v1/admin/ 경로에 ExamAdminViewSet을 연결합니다.
    path("exams", ExamAdminListCreateAPIView.as_view(), name="exam"),
    path("exams/deployments", DeploymentListCreateAPIView.as_view(), name="exam-deployments"),
    path("exams/submissions", AdminSubmissionListAPIView.as_view(), name="exam-submission"),
    path(
        "exams/submissions/<int:submission_id>", ExamAdminSubmissionDetailView.as_view(), name="exam_submission_detail"
    ),
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
    path("exams/<int:pk>", ExamAdminRetrieveUpdateDestroyAPIView.as_view(), name="exam-detail"),
    path("exams/<int:exam_id>/questions", ExamAdminQuestionCreateAPIView.as_view(), name="exam-questions"),
    path(
        "exams/questions/<int:question_id>",
        ExamAdminQuestionUpdateDestroyAPIView.as_view(),
        name="exam-questions-detail",
    ),
]

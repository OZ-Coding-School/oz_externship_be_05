from django.urls import URLPattern, URLResolver, path

from apps.exams.views.admin import (
    AdminDeploymentDetailUpdateDeleteView,
    DeploymentListCreateAPIView,
    ExamAdminListCreateAPIView,
    ExamAdminQuestionUpdateDestroyAPIView,
    ExamAdminRetrieveUpdateDestroyAPIView,
    ExamDeploymentStatusAPIView,
)

urlpatterns: list[URLPattern | URLResolver] = [
    # /api/v1/admin/exams/ 경로에 ExamAdminViewSet을 연결합니다.
    path("", ExamAdminListCreateAPIView.as_view(), name="exam"),
    path("deployments/", DeploymentListCreateAPIView.as_view(), name="exam-deployments"),
    path(
        "deployments/<int:deployment_id>/",
        AdminDeploymentDetailUpdateDeleteView.as_view(),
        name="exam-deployment-detail",
    ),
    path(
        "deployments/<int:deployment_id>/status/", ExamDeploymentStatusAPIView.as_view(), name="exam-deployment-status"
    ),
    path("<int:pk>/", ExamAdminRetrieveUpdateDestroyAPIView.as_view(), name="exam-detail"),
    path("questions/<int:question_id>/", ExamAdminQuestionUpdateDestroyAPIView.as_view(), name="exam-questions-detail"),
]

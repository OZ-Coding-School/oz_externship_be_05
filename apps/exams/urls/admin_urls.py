from django.urls import URLPattern, URLResolver, path

from apps.exams.views.admin import (
    AdminDeploymentDetailUpdateDeleteView,
    DeploymentListCreateAPIView,
    ExamAdminListCreateAPIView,
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
    path("<str:pk>/", ExamAdminRetrieveUpdateDestroyAPIView.as_view(), name="exam-detail"),
]

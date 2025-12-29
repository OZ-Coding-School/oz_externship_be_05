from django.urls import URLPattern, URLResolver, path

from apps.exams.views.student import (
    ExamAccessCodeVerifyView,
    ExamDeploymentStatusCheckView,
    ExamQuestionView,
    ExamResultView,
    ExamSubmissionCreateAPIView,
)

urlpatterns: list[URLPattern | URLResolver] = [
    path(
        # student/submit
        "submissions",
        ExamSubmissionCreateAPIView.as_view(),
        name="exam_submit",
    ),
    path(
        # student/result
        "submissions/<int:submission_id>",
        ExamResultView.as_view(),
        name="exam_result",
    ),
    path(
        "deployments/<int:deployment_id>/check-code",
        ExamAccessCodeVerifyView.as_view(),
        name="exam_check_code",
    ),
    path(
        "deployments/<int:deployment_id>",
        ExamQuestionView.as_view(),
        name="exam_taking",
    ),
    path(
        "deployments/<int:deployment_id>/status", ExamDeploymentStatusCheckView.as_view(), name="exam_checking_status"
    ),
]

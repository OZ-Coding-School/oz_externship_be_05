from django.urls import URLPattern, URLResolver, path

from apps.exams.views.student import (
    ExamAccessCodeVerifyView,
    ExamCheatingCheckView,
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
    path("deployments/<int:deployment_id>/cheating", ExamCheatingCheckView.as_view(), name="exam_cheating_check"),
]

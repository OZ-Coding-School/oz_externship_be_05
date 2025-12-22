from django.urls import URLPattern, URLResolver, path

from ..views.student.exam_result_view import ExamResultView
from ..views.student.exam_submit_view import ExamSubmissionCreateAPIView

urlpatterns: list[URLPattern | URLResolver] = [
    path(
        # student/submit
        "submissions/",
        ExamSubmissionCreateAPIView.as_view(),
        name="exam_submit",
    ),
    path(
        # student/result
        "submissions/<int:submission_id>",
        ExamResultView.as_view(),
        name="exam_result",
    ),
]

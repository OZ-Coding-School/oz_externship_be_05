from django.urls import URLPattern, URLResolver, path
from ..views.student.exam_submit_view import ExamSubmissionCreateAPIView

urlpatterns: list[URLPattern | URLResolver] = [
    path(
        # student/submit
        "deployment/<int:depolyment_pk>/submit/", ExamSubmissionCreateAPIView.as_view(), name="exam_submit",
    )
]

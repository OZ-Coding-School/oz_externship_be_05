from django.urls import path

from apps.qna.views.question.question_api import QuestionAPIView
from apps.qna.views.question.question_detail import QuestionDetailAPIView

urlpatterns = [
    path("questions", QuestionAPIView.as_view(), name="questions"),
    path("questions/<int:question_id>", QuestionDetailAPIView.as_view(), name="question_detail"),
]

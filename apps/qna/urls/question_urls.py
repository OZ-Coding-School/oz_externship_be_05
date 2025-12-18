from django.urls import path

from apps.qna.views.question.question_api import QuestionAPIView

urlpatterns = [
    path("questions", QuestionAPIView.as_view(), name="questions"),
]

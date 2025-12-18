from django.urls import path

from apps.qna.views.question.question_api import QuestionAPIView
from apps.qna.views.question.question_detail_api import QuestionDetailAPIView

urlpatterns = [
    path("questions", QuestionAPIView.as_view(), name="questions"),
    path("questions/<int:pk>", QuestionDetailAPIView.as_view(), name="question_detail"),
]

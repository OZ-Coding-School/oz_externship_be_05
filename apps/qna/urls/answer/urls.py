from django.urls import path

from apps.qna.specs.answers.views import (
    AnswerListCreateSpecAPIView,
    AnswerRetrieveUpdateSpecAPIView,
)
from apps.questions.spec.views import QuestionCreateSpecAPIView

urlpatterns = [
    path("", AnswerListCreateSpecAPIView.as_view()),
    path("<int:pk>/", AnswerRetrieveUpdateSpecAPIView.as_view()),
]

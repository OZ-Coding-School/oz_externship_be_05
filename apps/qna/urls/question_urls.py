from django.urls import path

from apps.qna.spec.question.spec_question_create.views import QuestionCreateSpecAPIView
from apps.qna.views.question.question_create import QuestionCreateAPIView

urlpatterns = [
    path("questions", QuestionCreateAPIView.as_view(), name="question_create"),
]

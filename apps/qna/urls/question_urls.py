from django.urls import path

from apps.qna.spec.question.spec_question_create.views import QuestionCreateSpecAPIView

urlpatterns = [
    path("questions", QuestionCreateSpecAPIView.as_view(), name="spec_question_create"),
]

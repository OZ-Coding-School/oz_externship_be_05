from django.urls import path

from apps.questions.spec.views import QuestionCreateSpecAPIView

urlpatterns = [
    path("questions", QuestionCreateSpecAPIView.as_view(), name="spec_question_create"),
]

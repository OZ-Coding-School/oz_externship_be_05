from django.urls import path

from apps.questions.spec.spec_question_create.views import QuestionCreateSpecAPIView
from apps.questions.views import QuestionCreateAPIView

urlpatterns = [
    # Spec
    path("questions/spec", QuestionCreateSpecAPIView.as_view(), name="spec_question_create"),
    # API
    path("questions", QuestionCreateAPIView.as_view()),
]

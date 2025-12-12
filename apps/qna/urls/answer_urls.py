from django.urls import path

from apps.qna.spec.answer.views import (
    AnswerListCreateSpecAPIView,
    AnswerRetrieveUpdateSpecAPIView,
)

urlpatterns = [
    path("", AnswerListCreateSpecAPIView.as_view()),
    path("<int:pk>/", AnswerRetrieveUpdateSpecAPIView.as_view()),
]

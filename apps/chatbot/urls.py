from django.urls import path

from apps.chatbot.views.session_views import (
    SessionCreateListAPIView,
    SessionDeleteView,
)

app_name = "chatbot"

urlpatterns = [
    path("sessions", SessionCreateListAPIView.as_view(), name="session-list-create"),
    path("sessions/<int:session_id>", SessionDeleteView.as_view(), name="session-delete"),
]

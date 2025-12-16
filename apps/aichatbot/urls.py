from django.urls import path

from apps.aichatbot.views.session_views import (
    SessionCreateListAPIView,
    SessionDeleteView,
)

app_name = "aichatbot"

urlpatterns = [
    path("sessions", SessionCreateListAPIView.as_view(), name="session-list-create"),
    path("sessions/<int:session_id>", SessionDeleteView.as_view(), name="session-delete"),
]

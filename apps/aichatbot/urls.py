from django.urls import path

from apps.aichatbot.views.session_views import (
    SessionCreateListAPIView,
    SessionDeleteView,
)

urlpatterns = [
    path("sessions", SessionCreateListAPIView.as_view(), name="spec-session-create-list"),
    path("sessions/<int:session_id>", SessionDeleteView.as_view(), name="spec-session-delete"),
]

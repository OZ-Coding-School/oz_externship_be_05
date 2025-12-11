from django.urls import path

from apps.aichatbot.models.chatbot_sessions import ChatbotSession
from apps.aichatbot.views import SessionDetailView, SessionGenerator, SessionListView

urlpatterns = [
    path("sessions", SessionGenerator.as_view(), name="spec_session_generator"),
    path("sessions/list", SessionListView.as_view(), name="spec_ChatbotSession"),
    path("sessions/<int:session_id>", SessionDetailView.as_view(), name="spec_ChatbotSessionDetail"),
]

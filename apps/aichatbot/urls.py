from django.urls import path

from apps.aichatbot.models.chatbot_sessions import ChatbotSession
from apps.aichatbot.views import SessionGenerator, SessionListView

urlpatterns = [
    path("", SessionGenerator.as_view(), name="spec_session_generator"),
    path("/chatbotsession", SessionListView.as_view(), name="spec_ChatbotSession"),
]

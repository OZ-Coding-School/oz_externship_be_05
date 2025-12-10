from django.urls import path

from apps.aichatbot.views import SessionGenerator, SessionListView

urlpatterns = [
    path("aichat", SessionGenerator.as_view(), name="spec_session_generator"),
    path("aichat", SessionListView.as_view(), name="spec_SessionList"),
]

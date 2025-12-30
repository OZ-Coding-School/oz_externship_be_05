from typing import cast

from django.contrib.auth import authenticate
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet
from rest_framework.exceptions import NotFound, NotAuthenticated
from rest_framework.pagination import CursorPagination
from rest_framework.request import Request

from apps.chatbot.models.chatbot_completions import ChatbotCompletion
from apps.chatbot.models.chatbot_sessions import ChatbotSession
from apps.core.exceptions.exception_messages import EMS
from apps.user.models import User


# Chatbot 전용 커서 페이지네이션
class ChatbotCursorPagination(CursorPagination):
    cursor_query_param = "cursor"
    page_size_query_param = "page_size"
    page_size = 10
    max_page_size = 50
    ordering = "-created_at"


class ChatbotSessionMixin:
    """
    ChatbotSession 공통 로직 제공
        - get_user(): 현재 인증된 사용자 반환
        - get_session_queryset(): 사용자의 모든 세션 QuerySet 반환
        - get_session(session_id): 특정 세션 조회 + EMS 404 처리
    """

    request: Request

    def get_user(self) -> User:
        user = self.request.user
        if not user.is_authenticated:
            raise NotAuthenticated(EMS.E401_NO_AUTH_DATA)
        return user

    def get_session_queryset(self) -> QuerySet[ChatbotSession]:
        return ChatbotSession.objects.filter(user=self.get_user())

    def get_session(self, session_id: int) -> ChatbotSession:
        session = self.get_session_queryset().filter(id=session_id).first()
        if session is None:
            raise NotFound(EMS.E404_CHATBOT_SESSION_NOT_FOUND)
        return session


class ChatbotCompletionMixin(ChatbotSessionMixin):
    """
    ChatbotCompletion 공통 로직 제공 Mixin
    ChatbotSessionMixin 상속->세션 관련 기능포함
        - (상속) get_user()
        - (상속) get_session_queryset()
        - (상속) get_session(session_id)
        - get_completion_queryset(session): 세션의 모든 메시지 QuerySet 반환
    """

    def get_completion_queryset(self, session: ChatbotSession) -> QuerySet[ChatbotCompletion]:
        return session.messages.all()

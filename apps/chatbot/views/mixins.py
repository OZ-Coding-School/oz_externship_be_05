from django.db.models import QuerySet
from rest_framework.exceptions import NotAuthenticated, NotFound
from rest_framework.pagination import CursorPagination
from rest_framework.request import Request

from apps.chatbot.models.chatbot_completions import ChatbotCompletion
from apps.chatbot.models.chatbot_sessions import ChatbotSession
from apps.core.exceptions.exception_messages import EMS
from apps.user.models import User

"""
Chatbot Views Mixins
    ChatbotCursorPagination: 커서 기반 페이지네이션 (page_size=10, ordering=-created_at)
    ChatbotSessionMixin: 세션 공통 로직
    ChatbotCompletionMixin(ChatbotSessionMixin): 메시지 공통 로직
"""

"""
ChatbotCursorPagination: 커서 기반 페이지네이션 (page_size=10, ordering=-created_at)
"""


class ChatbotCursorPagination(CursorPagination):
    cursor_query_param = "cursor"
    page_size_query_param = "page_size"
    page_size = 10
    max_page_size = 50
    ordering = "-created_at"


"""
ChatbotSessionMixin: 세션 공통 로직. 모두 상속
    get_user          - 인증된 사용자 반환 (미인증 시 401)
    get_session_queryset - 사용자의 모든 세션 QuerySet
    get_session       - 특정 세션 조회 (없으면 404)
"""


class ChatbotSessionMixin:
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


"""
ChatbotCompletionMixin(ChatbotSessionMixin): 메시지 공통 로직
    get_completion_queryset - 세션의 모든 메시지 QuerySet
"""


class ChatbotCompletionMixin(ChatbotSessionMixin):
    def get_completion_queryset(self, session: ChatbotSession) -> QuerySet[ChatbotCompletion]:
        return session.messages.all()

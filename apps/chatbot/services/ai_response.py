from __future__ import annotations

from apps.chatbot.models.chatbot_completions import ChatbotCompletion, UserRole
from apps.chatbot.models.chatbot_sessions import ChatbotSession


# ai 챗봇 답변. 실서비스 시 외부 모델 연동 로직을 해당 모듈에서 작업.
def ai_chat_response(*, session: ChatbotSession, user_message: str) -> ChatbotCompletion:
    # 차후 기능 확장 예정
    ai_response = f"Reply to '{user_message}'"

    return ChatbotCompletion.objects.create(
        session=session,
        message=ai_response,
        role=UserRole.ASSISTANT,
    )

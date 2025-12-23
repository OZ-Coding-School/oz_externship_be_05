from __future__ import annotations
import json
import os
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Iterable

import google.generativeai as genai
from asgiref.sync import sync_to_async
from django.http import StreamingHttpResponse

from apps.chatbot.models.chatbot_completions import ChatbotCompletion, UserRole
from apps.chatbot.models.chatbot_sessions import ChatbotSession, ChatModel

if TYPE_CHECKING:
    from google.generativerai.types import GenerateContentResponses

# Gemini API 설정
# TODO: API 키 넣기 (실제 환경에서는 환경변수로 관리할 것)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "123456")  # 임시
genai.configure(api_key=GEMINI_API_KEY)

# SSE 포멧 인코딩
def _sse_encode(data: str) -> str:
    return f"data: {data}\n\n"

# SSE 메세지, JSON 형태로 생성
def _sse_json(content: str, *, done: bool = False, error: bool = False) -> str:
    if done:
        return _sse_encode("[DONE]")
    if error:
        return _sse_encode("[ERROR]")
    return _sse_encode(json.dumps({"content": content}, ensure_ascii=False))

# 유저 메세지 DB 저장
def user_message_save(*, session: ChatbotSession, message: str) -> ChatbotCompletion:
    return ChatbotCompletion.objects.create(
        session=session,
        message=message,
        role=UserRole.USER,
    )

# ai 메세지 DB 저장
def ai_message_save(*, session: ChatbotSession, message: str) -> ChatbotCompletion:
    return ChatbotCompletion.objects.create(
        session=session,
        message=message,
        role=UserRole.ASSISTANT,
    )

# 세션 대화 이력 Gemini API 형식으로 변환
def get_chat_history(session: ChatbotSession) -> list[dict[str, str]]:
    completions = session.messages.all().order_by("-created_at")
    history = []

    for completion in completions:
        role = "model" if completion.role == UserRole.ASSISTANT else "user"
        history.append({
            "role": role,
            "parts": [completion.message],
        })
    return history

# 비동기 전환
@sync_to_async
def async_user_message_save(*, session: ChatbotSession, message: str) -> ChatbotCompletion:
    return user_message_save(session=session, message=message)

@sync_to_async
def async_ai_message_save(*, session: ChatbotSession, message: str) -> ChatbotCompletion:
    return ai_message_save(session=session, message=message)

@sync_to_async
def async_get_chat_history(session: ChatbotSession) -> list[dict[str, str]]:
    return get_chat_history(session=session)

# 제미나이 모델 인스턴스 반환
def get_gemini_model(model_name: str = "gemini-2.0-flash") -> genai.GenerativeModel:
    return genai.GenerativeModel(model_name)

# 스트리밍 응답 생성 비동기 제너레이터
async def generate_streaming_response(*, session: ChatbotSession, user_message: str) -> AsyncIterator[str]:
    buffer: list[str] = []

    try:
        history = await async_get_chat_history(session)

        model = get_gemini_model()
        chat = model.start_chat(history=history)

        # 스트리밍 응답 생성: Gemini send-message : 등기 → 래핑 필요함
        @sync_to_async
        def send_message_stream() -> Iterable[GenerateContentResponse]:
            return chat.send_message(user_message, stream=True)

        response = await send_message_stream()

        @sync_to_async
        def get_chunk() -> list[str]:
            chunks = []
            for chunk in response:
                if chunk.text:
                    chunk.append(chunk.text)
            return chunks

        chunks = await get_chunk()

        for chunk_text in chunks:
            buffer.append(chunk_text)
            yield _sse_json(chunk_text)

        full_response = "".join(buffer)
        if full_response:
            await async_ai_message_save(session=session, message=full_response)

        yield _sse_json("", done=True)

    except Exception as e:
        print(f"Gemini Streaming Error: {type(e).__name__}: {e}")
        yield _sse_json("", error=True)

# StreamingHttpResponse 생성
async def create_streaming_response(*, session: ChatbotSession, user_message: str) -> StreamingHttpResponse:
    response = StreamingHttpResponse(
        generate_streaming_response(session=session, user_message=user_message),
        context_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
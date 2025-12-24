from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterator

from django.http import StreamingHttpResponse
from google import genai
from google.genai import types

from apps.chatbot.models.chatbot_completions import ChatbotCompletion, UserRole
from apps.chatbot.models.chatbot_sessions import ChatbotSession

logger = logging.getLogger(__name__)

# Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = "gemini-2.0-flash"


def _get_client() -> genai.Client:
    return genai.Client(api_key=GEMINI_API_KEY)


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
def get_chat_history(session: ChatbotSession) -> list[types.Content]:
    completions = session.messages.all().order_by("created_at")
    history = []

    for completion in completions:
        role = "model" if completion.role == UserRole.ASSISTANT else "user"
        history.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=completion.message)],
            )
        )
    return history


# (제너레이터에서 분리)
def _build_contents(*, session: ChatbotSession, user_message: str) -> list[types.Content]:
    contents = get_chat_history(session)
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)],
        )
    )
    return contents


# (제너레이터에서 분리) Gemini Streaming 결과: 텍스트 chunk만 뽑아 동기 iterator로 제공
def _iter_gemini_text_stream(*, contents: list[types.Content]) -> Iterator[str]:
    client = _get_client()
    for chunk in client.models.generate_content_stream(
        model=DEFAULT_MODEL,
        contents=contents,  # type: ignore[arg-type]
    ):
        text = getattr(chunk, "text", None)
        if text:
            yield text


# 스트리밍 응답 생성 동기 제너레이터 (chunk 받는 즉시 yield, 전체 응답 buffer 모으고 마지막에 DB 저장)
def generate_streaming_response(*, session: ChatbotSession, user_message: str) -> Iterator[str]:
    buffer: list[str] = []
    try:
        contents = _build_contents(session=session, user_message=user_message)
        for chunk_text in _iter_gemini_text_stream(contents=contents):
            buffer.append(chunk_text)
            yield _sse_json(chunk_text)

        full_response = "".join(buffer)
        if full_response:
            ai_message_save(session=session, message=full_response)

        yield _sse_json("", done=True)

    except Exception as e:
        logger.exception("Gemini Streaming Error: %s: %s", type(e).__name__, e)
        print(f"Gemini Streaming Error: {type(e).__name__}: {e}")
        yield _sse_json("", error=True)
        yield _sse_json("", done=True)


# StreamingHttpResponse 생성 (async 삭제)
def create_streaming_response(*, session: ChatbotSession, user_message: str) -> StreamingHttpResponse:
    response = StreamingHttpResponse(
        streaming_content=generate_streaming_response(session=session, user_message=user_message),
        content_type="text/event-stream; charset=utf-8",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    response["Connection"] = "keep-alive"
    return response

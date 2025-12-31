from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterator
from typing import Any, cast

from django.http import StreamingHttpResponse
from google import genai
from google.genai import types

from apps.chatbot.models.chatbot_completions import ChatbotCompletion, UserRole
from apps.chatbot.models.chatbot_sessions import ChatbotSession

logger = logging.getLogger(__name__)

"""
Gemini API SSE 스트리밍 서비스

SSEEncoder: SSE 포맷 인코딩
GeminiStreamingService: Gemini API 스트리밍 처리
Functions:
    user_message_save: 사용자 메시지 DB 저장
    ai_message_save: AI 메시지 DB 저장
    create_streaming_response: StreamingHttpResponse 생성
"""

"""
SSEEncoder: SSE 포맷 인코딩
    encode: SSE 포맷 인코딩
    json: SSE JSON 메시지 생성 (content/done/error)
"""


class SSEEncoder:
    @staticmethod
    def encode(data: str) -> str:
        return f"data: {data}\n\n"

    @staticmethod
    def json(content: str, *, done: bool = False, error: bool = False) -> str:
        if done:
            return SSEEncoder.encode("[DONE]")
        if error:
            return SSEEncoder.encode("[ERROR]")
        return SSEEncoder.encode(json.dumps({"content": content}, ensure_ascii=False))


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


"""
GeminiStreamingService: Gemini API 스트리밍 처리
    _get_api_key: 환경변수에서 GEMINI_API_KEY 조회
    _get_client: Gemini Client 인스턴스 생성
    get_chat_history: 세션 대화 이력 → Gemini API 형식 변환
    _build_contents: 대화 이력 + 새 메시지 → contents 생성
    _iter_gemini_text_stream: Gemini 스트리밍 텍스트 iterator
"""


class GeminiStreamingService:
    def __init__(self, session: ChatbotSession) -> None:
        self.session = session
        self.model = session.using_model

    @staticmethod
    def _get_api_key() -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        return api_key

    @staticmethod
    def _get_client() -> genai.Client:
        return genai.Client(api_key=GeminiStreamingService._get_api_key())

    # 세션 대화 이력 Gemini API 형식으로 변환
    def get_chat_history(self) -> list[types.Content]:
        completions = self.session.messages.all().order_by("created_at")
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
    def _build_contents(self, user_message: str) -> list[types.Content]:
        contents = self.get_chat_history()
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)],
            )
        )
        return contents

    # (제너레이터에서 분리) Gemini Streaming 결과: 텍스트 chunk만 뽑아 동기 iterator로 제공
    def _iter_gemini_text_stream(self, contents: list[types.Content]) -> Iterator[str]:
        client = self._get_client()
        api_contents = cast(Any, contents)  # 타입 넓혀서 전달

        for chunk in client.models.generate_content_stream(
            model=self.model,
            contents=api_contents,
        ):
            text = getattr(chunk, "text", None)
            if text:
                yield text

    # 스트리밍 응답 생성 동기 제너레이터 (chunk 받는 즉시 yield, 전체 응답 buffer 모으고 마지막에 DB 저장)
    def generate_streaming_response(self, user_message: str) -> Iterator[str]:
        buffer: list[str] = []
        try:
            contents = self._build_contents(user_message)
            for chunk_text in self._iter_gemini_text_stream(contents):
                buffer.append(chunk_text)
                yield SSEEncoder.json(chunk_text)

            full_response = "".join(buffer)
            if full_response:
                ai_message_save(session=self.session, message=full_response)

            yield SSEEncoder.json("", done=True)

        except Exception as e:
            logger.exception("Gemini Streaming Error: %s: %s", type(e).__name__, e)
            yield SSEEncoder.json("", error=True)
            yield SSEEncoder.json("", done=True)
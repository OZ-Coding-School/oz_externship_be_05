from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from django.http import StreamingHttpResponse
from google.genai import types
from rest_framework.test import APITestCase

from apps.chatbot.models.chatbot_completions import ChatbotCompletion, UserRole
from apps.chatbot.models.chatbot_sessions import ChatbotSession, ChatModel
from apps.chatbot.services.completion_response_service import (
    GeminiStreamingService,
    SSEEncoder,
    ai_message_save,
    user_message_save,
)
from apps.qna.models import Question, QuestionCategory
from apps.user.models import User

"""
completion_response_service 테스트

SSEEncoder: SSE 인코딩 테스트
GeminiStreamingService: 스트리밍 서비스 테스트
Functions: user_message_save, ai_message_save, create_streaming_response
"""


class CompletionResponseServiceTests(APITestCase):
    user: User
    password: str
    question_category: QuestionCategory
    question: Question
    session: ChatbotSession

    @classmethod
    def setUpTestData(cls) -> None:
        cls.password = "00000000"  # 해싱용 password 설정, 로그인 대비
        # 유저 생성
        cls.user = User.objects.create_user(
            email="test@example.com",
            password=cls.password,
            name="testuser",
            nickname="testuser",
            birthday=date(2000, 1, 1),
        )

        cls.question_category = QuestionCategory.objects.create(
            name="test_category",
        )

        # 질문 생성
        cls.question = Question.objects.create(
            author=cls.user,
            category=cls.question_category,
            title="테스트 질문",
            content="테스트용 질문입니다.",
        )

        # 세션 생성
        cls.session = ChatbotSession.objects.create(
            user=cls.user,
            question=cls.question,
            title="테스트 세션",
            using_model=ChatModel.GEMINI,
        )

    # 테스트 간 간섭 방지용. 같은 세션 completion 초기화.
    def setUp(self) -> None:
        ChatbotCompletion.objects.filter(session=self.session).delete()

    # Server-Sent Event 체크
    def test_sse_encode(self) -> None:
        self.assertEqual(SSEEncoder.encode("hello"), "data: hello\n\n")
        self.assertEqual(SSEEncoder.encode(""), "data: \n\n")

    def test_sse_json(self) -> None:
        # 일반 content
        self.assertEqual(SSEEncoder.json("테스트"), 'data: {"content": "테스트"}\n\n')
        # done / error
        self.assertEqual(SSEEncoder.json("", done=True), "data: [DONE]\n\n")
        self.assertEqual(SSEEncoder.json("", error=True), "data: [ERROR]\n\n")
        # done 우선
        self.assertEqual(SSEEncoder.json("x", done=True, error=True), "data: [DONE]\n\n")
        # ensure_ascii=False 기대
        self.assertNotIn("\\u", SSEEncoder.json("한글"))

    # DB 저장 확인
    def test_user_message_save(self) -> None:
        c = user_message_save(session=self.session, message="hi")
        self.assertEqual(c.session_id, self.session.id)
        self.assertEqual(c.role, UserRole.USER)
        self.assertEqual(c.message, "hi")

    def test_ai_message_save(self) -> None:
        c = ai_message_save(session=self.session, message="hello")
        self.assertEqual(c.session_id, self.session.id)
        self.assertEqual(c.role, UserRole.ASSISTANT)
        self.assertEqual(c.message, "hello")

    # 컨텐츠 확인
    def test_get_chat_history_empty(self) -> None:
        service = GeminiStreamingService(self.session)
        history = service.get_chat_history()
        self.assertEqual(history, [])

    def test_build_contents_appends_user_message(self) -> None:
        # 이전 메시지 1개
        ChatbotCompletion.objects.create(session=self.session, message="이전", role=UserRole.USER)

        service = GeminiStreamingService(self.session)
        contents = service._build_contents(user_message="새 메시지")
        self.assertGreaterEqual(len(contents), 2)

        last = contents[-1]
        self.assertEqual(last.role, "user")

        parts = last.parts
        self.assertIsNotNone(parts)
        assert parts is not None  # mypy용

        self.assertGreaterEqual(len(parts), 1)
        self.assertEqual(parts[0].text, "새 메시지")

    @patch.object(GeminiStreamingService, "_get_client")
    def test_iter_gemini_text_stream_yields_only_text(self, mock_get_client: MagicMock) -> None:
        # chunk.text가 None이면 필터링되어야 함
        mock_chunk1 = MagicMock(text="Hello ")
        mock_chunk2 = MagicMock(text=None)
        mock_chunk3 = MagicMock(text="World")

        mock_client = MagicMock()
        mock_client.models.generate_content_stream.return_value = [mock_chunk1, mock_chunk2, mock_chunk3]
        mock_get_client.return_value = mock_client

        contents = [
            types.Content(role="user", parts=[types.Part.from_text(text="ping")]),
        ]

        service = GeminiStreamingService(self.session)
        out = list(service._iter_gemini_text_stream(contents=contents))
        self.assertEqual(out, ["Hello ", "World"])

    @patch.object(GeminiStreamingService, "_iter_gemini_text_stream")
    def test_generate_streaming_response_success_saves_full_message(self, mock_iter: MagicMock) -> None:
        mock_iter.return_value = iter(["Hello ", "World"])

        service = GeminiStreamingService(self.session)
        out = list(service.generate_streaming_response(user_message="테스트"))
        self.assertEqual(out[0], SSEEncoder.json("Hello "))
        self.assertEqual(out[1], SSEEncoder.json("World"))
        self.assertEqual(out[-1], "data: [DONE]\n\n")

        saved = ChatbotCompletion.objects.filter(session=self.session, role=UserRole.ASSISTANT).first()
        self.assertIsNotNone(saved)
        assert saved is not None  # mypy용
        self.assertEqual(saved.message, "Hello World")

    @patch.object(GeminiStreamingService, "_iter_gemini_text_stream")
    def test_generate_streaming_response_empty_does_not_save(self, mock_iter: MagicMock) -> None:
        mock_iter.return_value = iter([])

        service = GeminiStreamingService(self.session)
        out = list(service.generate_streaming_response(user_message="테스트"))
        self.assertEqual(out, ["data: [DONE]\n\n"])

        self.assertEqual(
            ChatbotCompletion.objects.filter(session=self.session, role=UserRole.ASSISTANT).count(),
            0,
        )

from unittest.mock import MagicMock, patch

from rest_framework import status

from apps.chatbot.models.chatbot_completions import ChatbotCompletion, UserRole
from apps.chatbot.tests.completion.api.test_completion_api_base import (
    CompletionAPITestBase,
)

"""
/sessions/{session_id}/completions/
POST 테스트: AI 응답 생성(+SSE 스트리밍)을 포함한 채팅 메세지 보내기 기능
base에 있는 추상화 메서드: post_response 사용!

test_completion_create_400_missing_message
    메세지 필드 누락 시 400 반환

test_completion_create_400_empty_message
    메세지 필드가 빈 문자열일 때 400 반환

test_completion_create_401_unauthenticated
    미인증 시 401 반환

test_completion_create_404_session_notfound
    존재하지 않는 세션 id로 요청하면 404 반환

test_completion_create_404_other_session
    타인 세션 접근 시 400 반환

"""


# POST 테스트
class CompletionCreateAPITest(CompletionAPITestBase):

    @patch("apps.chatbot.services.completion_response_service._iter_gemini_text_stream")
    def test_completion_create_200(self, mock_stream: MagicMock) -> None:
        mock_stream.return_value = iter(["Greetings", "World"])
        response = self.post_response(self.session.id, "Hello World")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/event-stream; charset=utf-8")

        # 스트리밍 응답 내용 확인
        content = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn("data:", content)
        self.assertIn("[DONE]", content)

        # 사용자 메시지 DB 저장 확인
        user_message = ChatbotCompletion.objects.filter(
            session=self.session,
            role=UserRole.USER,
        ).first()
        self.assertIsNotNone(user_message)
        assert isinstance(user_message, ChatbotCompletion)
        self.assertEqual(user_message.message, "Hello World")

        # AI 메시지 DB 저장 확인
        ai_message = ChatbotCompletion.objects.filter(
            session=self.session,
            role=UserRole.ASSISTANT,
        ).first()

        assert isinstance(ai_message, ChatbotCompletion)
        self.assertIsNotNone(ai_message)
        self.assertEqual(ai_message.message, "GreetingsWorld")

    def test_completion_create_400_missing_message(self) -> None:
        response = self.post_response(self.session.id, message=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_completion_create_400_empty_message(self) -> None:
        response = self.post_response(self.session.id, message="")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_completion_create_401_unauthenticated(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.post_response(self.session.id, "Hello World from unwelcomed")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_completion_create_404_session_notfound(self) -> None:
        invalid_session_id = self.session.id + 999
        response = self.post_response(invalid_session_id, "Bad World")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_completion_create_404_other_session(self) -> None:
        response = self.post_response(self.session.id, "From Other World")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

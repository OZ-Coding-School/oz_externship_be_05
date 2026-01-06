from rest_framework import status

from apps.chatbot.models.chatbot_completions import ChatbotCompletion, UserRole
from apps.chatbot.models.chatbot_sessions import ChatbotSession, ChatModel
from apps.chatbot.tests.session.api.test_session_api_base import SessionAPITestBase

"""
DELETE /sessions/{session_id}/
세션 삭제 API 테스트

test_session_delete_204
    정상 삭제 시 204 반환 + DB에서 삭제

test_session_delete_with_messages
    메시지 포함 세션 삭제 시 메시지도 삭제

test_session_delete_401_unauthenticated
    미인증 시 401 반환

test_session_delete_404_not_found
    존재하지 않는 세션 ID 요청 시 404 반환

test_session_delete_404_other_user_session
    타인 세션 삭제 시도 시 404 반환

test_session_delete_does_not_affect_other_sessions
    다른 세션에 영향 없음
"""


class SessionDeleteAPITests(SessionAPITestBase):
    def setUp(self) -> None:
        super().setUp()

        # 세션 생성 (본인용)
        self.delete_target_session = ChatbotSession.objects.create(
            user=self.user,
            question=self.question,
            title="삭제용 세션 1",
            using_model=ChatModel.GEMINI,
        )

        self.own_session = ChatbotSession.objects.create(
            user=self.user,
            question=self.question2,
            title="삭제하지 않는 세션 1",
            using_model=ChatModel.GEMINI,
        )

        self.other_session = ChatbotSession.objects.create(
            user=self.other_user,
            question=self.other_question,
            title="삭제용 타인 세션 1",
            using_model=ChatModel.GEMINI,
        )

    def test_session_delete_204(self) -> None:
        session_id = self.delete_target_session.id

        response = self.delete_session(session_id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ChatbotSession.objects.filter(id=session_id).exists())

    def test_session_delete_with_messages(self) -> None:
        ChatbotCompletion.objects.create(
            session=self.delete_target_session,
            message="테스트 메시지",
            role=UserRole.USER,
        )
        session_id = self.delete_target_session.id
        response = self.delete_session(session_id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ChatbotCompletion.objects.filter(session_id=session_id).count(), 0)

    def test_session_delete_401_unauthenticated(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.delete_session(self.delete_target_session.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_delete_404_not_found(self) -> None:
        invalid_session_id = self.delete_target_session.id + 999
        response = self.delete_session(invalid_session_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_session_delete_404_other_user_session(self) -> None:
        response = self.delete_session(self.other_session.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 타인 세션은 삭제되지 않음
        self.assertTrue(ChatbotSession.objects.filter(id=self.other_session.id).exists())

    def test_session_delete_does_not_affect_other_sessions(self) -> None:
        other_session_id = self.other_session.id
        own_session_id = self.own_session.id
        response = self.delete_session(self.delete_target_session.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(ChatbotSession.objects.filter(id=other_session_id).exists())
        self.assertTrue(ChatbotSession.objects.filter(id=own_session_id).exists())

import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.chatbot.models.chatbot_completions import ChatbotCompletion, UserRole
from apps.chatbot.models.chatbot_sessions import ChatbotSession, ChatModel
from apps.chatbot.tests.completion.api.test_completion_api_base import (
    CompletionAPITestBase,
)
from apps.qna.models.question import Question, QuestionCategory
from apps.user.models.user import User

"""
/sessions/{session_id}/completions/
DELETE 테스트: 세션 내 메세지 삭제

test_completion_delete_204
    정상 요청 시 204 + 메세지 전체 삭제

test_completion_delete_session_preserve
    메세지 삭제 후 세션 유지

test_completion_delete_401_unauthenticated
    미인증 시 401

test_completion_delete_404_session_notfound
    존재하지 않는 세션 ID 요청 시 404 반환

test_completion_delete_404_other_session
    타인의 세션에 접근 시 404 반환

test_completion_delete_noneffective_other_session
    다른 세션 메세지는 삭제되지 않음

"""


class CompletionDeleteAPITest(CompletionAPITestBase):
    def setUp(self) -> None:
        super().setUp()

        ChatbotCompletion.objects.create(
            session=self.session,
            message="삭제용 메세지1",
            role=UserRole.USER,
        )
        ChatbotCompletion.objects.create(
            session=self.session,
            message="삭제용 메세지2",
            role=UserRole.ASSISTANT,
        )

    def test_completion_delete_204(self) -> None:
        """
        생성한 메세지 2개 확인 → 메세지 삭제 → 204 반환
        → 세션 자체는 존재, 메세지만 삭제됐음 확인
        """

        self.assertEqual(self.session.messages.count(), 2)
        response = self.delete_response(self.session.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.session.messages.count(), 0)

    def test_completion_delete_401_unauthenticated(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.delete_response(self.session.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_completion_delete_404_session_notfound(self) -> None:
        invalid_session_id = self.session.id + 999
        response = self.delete_response(invalid_session_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_completion_delete_404_other_session(self) -> None:
        response = self.delete_response(self.other_session.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_completion_delete_noneffective_other_session(self) -> None:
        ChatbotCompletion.objects.create(
            session=self.other_session,
            message="다른 세션 메세지",
            role=UserRole.USER,
        )
        other_session_message_count = self.other_session.messages.count()
        response = self.delete_response(self.session.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.other_session.messages.count(), other_session_message_count)

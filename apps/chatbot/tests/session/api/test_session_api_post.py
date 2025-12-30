# URL 연결 여부
# 유효한 요청에서 올바른 응답 body 반환 여부
# 잘못된 요청 시 적절한 status code 반환 여부
from typing import Any

from rest_framework import status

from apps.chatbot.models.chatbot_sessions import ChatbotSession, ChatModel
from apps.chatbot.tests.session.api.test_session_api_base import SessionAPITestBase

"""
POST /sessions/
세션 생성 API 테스트

test_session_create_201
    정상 요청 시 201 반환 + DB 저장

test_session_create_401_unauthenticated
    미인증 시 401 반환

test_session_create_400_question_not_exists
    존재하지 않는 question ID 요청 시 400/404 반환

test_session_create_400_missing_required_fields
    필수 필드 누락 시 400 반환
"""


class SessionCreateAPITest(SessionAPITestBase):
    def test_session_create_201(self) -> None:
        initial_count = ChatbotSession.objects.count()

        response = self.post_session(
            question_id=self.question.id,
            title="새로운 세션",
            using_model=ChatModel.GEMINI,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChatbotSession.objects.count(), initial_count + 1)

        # 생성된 세션 검증
        session = ChatbotSession.objects.latest("created_at")
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.question, self.question)
        self.assertEqual(session.title, "새로운 세션")
        self.assertEqual(session.using_model, ChatModel.OPENAI)

        # 응답 데이터 검증
        data = response.json()
        self.assertEqual(data["id"], session.id)
        self.assertEqual(data["user"], self.user.id)
        self.assertEqual(data["question"], self.question.id)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_session_create_401_unauthenticated(self) -> None:
        # 인증 해제
        self.client.force_authenticate(user=None)
        response = self.post_session(
            question_id=self.question.id,
            using_model=ChatModel.GEMINI,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_create_400_question_not_exists(self) -> None:
        invalid_question_id = self.question.id + 9999

        response = self.post_session(
            question_id=invalid_question_id,
            using_model=ChatModel.GEMINI
        )

        self.assertIn(
            response.status_code,
            {status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND},
        )

    def test_session_create_400_missing_required_fields(self) -> None:
        response = self.post_session()  # 아무 필드도 없이 요청

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

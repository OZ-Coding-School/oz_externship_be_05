from rest_framework import status

from apps.chatbot.models.chatbot_completions import ChatbotCompletion, UserRole
from apps.chatbot.tests.completion.api.test_completion_api_base import (
    CompletionAPITestBase,
)

"""
/sessions/{session_id}/completions/
GET 테스트: 메세지 목록 조회

test_completion_list_200
    정상 요청 시 200 + 메세지 목록 반환

test_completion_list_pagination
    페이지네이션 응답 구조 확인
    
test_completion_list_response_fields
    응답 필드 구조 확인
    
test_completion_list_returns_only_session_message
    해당 세션의 메세지만 반환
    
test_completion_list_401_unauthenticated
    미인증 시 401
    
test_completion_list_404_session_notfound
    존재하지 않는 세션 ID로 요청 시 404 반환
    
test_completion_list_404_other_session
    타인 세션에 접근 시 404 반환

"""


class CompletionListAPITest(CompletionAPITestBase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        ChatbotCompletion.objects.create(
            session=cls.session,
            message="사용자 메세지 1",
            role=UserRole.USER,
        )
        ChatbotCompletion.objects.create(
            session=cls.session,
            message="AI응답 메세지 1",
            role=UserRole.ASSISTANT,
        )
        ChatbotCompletion.objects.create(
            session=cls.session,
            message="사용자 메세지 2",
            role=UserRole.USER,
        )
        # 다른 세션 메세지
        ChatbotCompletion.objects.create(
            session=cls.other_session,
            message="사용자2 메세지1",
            role=UserRole.USER,
        )

    def test_completion_list_200(self) -> None:
        response = self.get_response(self.session.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 3)

    def test_completion_list_pagination(self) -> None:
        response = self.get_response(self.session.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

    def test_completion_list_response_fields(self) -> None:
        response = self.get_response(self.session.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        message = response.data["results"][0]
        self.assertIn("id", message)
        self.assertIn("message", message)
        self.assertIn("role", message)
        self.assertIn("created_at", message)

    def test_completion_list_returns_only_session_message(self) -> None:
        response = self.get_response(self.session.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = response.data["results"]
        for msg in messages:
            self.assertNotEqual(msg["message"], "타인의 메세지")

    def test_completion_list_401_unauthenticated(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.get_response(self.session.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_completion_list_404_session_notfound(self) -> None:
        invalid_session_id = self.session.id + 999
        response = self.get_response(invalid_session_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_completion_list_404_other_session(self) -> None:
        response = self.get_response(self.other_session.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

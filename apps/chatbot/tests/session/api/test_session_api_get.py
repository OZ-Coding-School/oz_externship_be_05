from rest_framework import status

from apps.chatbot.models.chatbot_sessions import ChatbotSession, ChatModel
from apps.chatbot.tests.session.api.test_session_api_base import SessionAPITestBase

"""
GET /sessions/
세션 목록 조회 API 테스트

test_session_list_200
    정상 요청 시 200 반환 + 세션 목록

test_session_list_returns_only_own_sessions
    본인 세션만 반환 (타인 세션 제외)

test_session_list_401_unauthenticated
    미인증 시 401 반환

test_session_list_pagination
    페이지네이션 응답 구조 확인

test_session_list_response_fields
    응답 필드 구조 확인

"""


class SessionListAPITest(SessionAPITestBase):

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        # 세션 생성 (본인용)
        ChatbotSession.objects.create(
            user=cls.user,
            question=cls.question,
            title="세션입니다",
            using_model=ChatModel.GEMINI,
        )

    def test_session_list_200(self) -> None:
        response = self.get_sessions()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_session_list_returns_only_own_sessions(self) -> None:
        response = self.get_sessions()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 본인 세션 개수 확인 (base에서 1개 + setUpTestData에서 1개 = 2개)
        own_session_count = ChatbotSession.objects.filter(user=self.user).count()
        self.assertEqual(len(response.data["results"]), own_session_count)

        # 타인 세션 제목이 없는지 확인
        for session in response.data["results"]:
            self.assertNotEqual(session["title"], "타인 세션")

    def test_session_list_pagination(self) -> None:
        response = self.get_sessions()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

    def test_session_list_response_fields(self) -> None:
        response = self.get_sessions()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)

        session = response.data["results"][0]
        self.assertIn("id", session)
        self.assertIn("user", session)
        self.assertIn("question", session)
        self.assertIn("title", session)
        self.assertIn("using_model", session)
        self.assertIn("created_at", session)
        self.assertIn("updated_at", session)

    def test_session_list_401_unauthenticated(self) -> None:
        self.client.force_authenticate(user=None)

        response = self.get_sessions()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)

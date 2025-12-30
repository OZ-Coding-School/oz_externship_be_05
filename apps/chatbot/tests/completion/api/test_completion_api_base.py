import datetime
from typing import Any
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.chatbot.models.chatbot_sessions import ChatbotSession, ChatModel
from apps.user.models.user import User
from apps.qna.models.question import QuestionCategory, Question
from apps.qna.models.question import Question

"""
completion API 테스트용 공통 설정
- 유저 생성
- 타 유저 생성
- 질문 카테고리 생성
- 질문 생성
- 본인 세션 생성
- 타 사용자 세션 생성

추상화 요청 메서드 사용: 
post_response
get_response
delete_response
"""

class CompletionAPITestBase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.password = "password1234"  # 해싱용 password 설정
        cls.user = User.objects.create_user(
            email="api_tester@example.com",
            password=cls.password,
            name="testuser",
            nickname="testuser",
            birthday=datetime.date(2000, 1, 1),
        )

        cls.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            name="otheruser",
            nickname="otheruser",
            birthday=datetime.date(2000, 1, 1),
        )

        cls.question_category = QuestionCategory.objects.create(
            name="test_category",
        )

        cls.question = Question.objects.create(
            author=cls.user,
            category=cls.question_category,
            title="API용 테스트 질문",
            content="API 테스트용 질문 내용입니다.",
        )

        cls.session = ChatbotSession.objects.create(
            user=cls.user,
            question=cls.question,
            title="내 세션",
            using_model=ChatModel.GEMINI,
        )

        cls.other_session = ChatbotSession.objects.create(
            user=cls.other_user,
            question=cls.question,
            title="다른 유저 세션",
            using_model=ChatModel.GEMINI,
        )

    def setUp(self) -> None:
        self.client.force_authenticate(self.user)

    def get_url(self, session_id: int) -> str:
        return reverse("chatbot:completion", kwargs={"session_id": session_id})

    def post_response(self, session_id: int, message: str | None = None, **kwargs: Any) -> Any:
        payload: dict[str, Any] = {}
        if message is not None:
            payload["message"] = message
        return self.client.post(self.get_url(session_id), payload, format='json', **kwargs)

    def get_response(self, session_id: int, **kwargs: Any) -> Any:
        return self.client.get(self.get_url(session_id), **kwargs)

    def delete_response(self, session_id: int, **kwargs: Any) -> Any:
        return self.client.delete(self.get_url(session_id), **kwargs)
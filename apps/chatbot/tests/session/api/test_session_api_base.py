import datetime
from typing import Any

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.chatbot.models.chatbot_sessions import ChatbotSession, ChatModel
from apps.qna.models import QuestionCategory
from apps.qna.models.question.question_base import Question
from apps.user.models import User

"""
Session API 테스트용 공통 설정
- 유저 생성
- 타 유저 생성
- 질문 카테고리 생성
- 질문 생성
- 본인 세션 생성
- 타 유저 세션 생성
- url 헬퍼 (create/delete로 나뉨)

추상화 요청 메서드 사용:
- post_session(): 세션 생성
- get_sessions(): 세션 목록 조회
- delete_session(): 세션 삭제
"""


class SessionAPITestBase(APITestCase):
    user: "User"
    other_user: "User"
    password: str
    question: Question
    question2: Question
    other_question: Question
    question_category: QuestionCategory

    @classmethod
    def setUpTestData(cls) -> None:
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
            password=cls.password,
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

        cls.question2 = Question.objects.create(
            author=cls.user,
            category=cls.question_category,
            title="API용 테스트 질문2",
            content="API 테스트용 질문 내용입니다.",
        )

        cls.other_question = Question.objects.create(
            author=cls.other_user,
            category=cls.question_category,
            title="API용 테스트 질문2",
            content="타 유저용 질문입니다.",
        )

    # 초기화 메서드. user를 인증 상태로(로그인 필요없게)
    def setUp(self) -> None:
        self.client.force_authenticate(self.user)

    def get_list_create_url(self) -> str:
        return reverse("chatbot:session-list-create")

    def get_delete_url(self, session_id: int) -> str:
        return reverse("chatbot:session-delete", kwargs={"session_id": session_id})

    def post_session(
        self,
        question_id: int | None = None,
        title: str | None = None,
        using_model: str | None = None,
        **kwargs: Any,
    ) -> Any:
        payload: dict[str, Any] = {}
        if question_id is not None:
            payload["question"] = question_id
        if title is not None:
            payload["title"] = title
        if using_model is not None:
            payload["using_model"] = using_model
        return self.client.post(self.get_list_create_url(), payload, format="json", **kwargs)

    def get_sessions(self, **kwargs: Any) -> Any:
        return self.client.get(self.get_list_create_url(), **kwargs)

    def delete_session(self, session_id: int, **kwargs: Any) -> Any:
        return self.client.delete(self.get_delete_url(session_id), **kwargs)

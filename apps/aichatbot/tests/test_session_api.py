import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.aichatbot.models.chatbot_sessions import ChatbotSession, ChatModel
from apps.qna.models import QuestionCategory
from apps.qna.models.question.question_base import Question
from apps.user.models import User


# URL 연결 여부
# 유효한 요청에서 올바른 응답 body 반환 여부
# 잘못된 요청 시 적절한 status code 반환 여부
class SessionCreateAPITests(APITestCase):
    user: "User"
    question_category: QuestionCategory
    question: Question
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create(
            email="api_tester@example.com", password="password1234", birthday=datetime.date(2000, 1, 1)
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

        cls.url = reverse("aichatbot:session-list-create")

    # 초기화 메서드. user를 인증 상태로(로그인 필요없게)
    def setUp(self) -> None:
        self.client.force_authenticate(self.user)

    # 정상 요청 시 201 응답.
    def test_session_create_201(self) -> None:

        payload: dict[str, Any] = {
            "question": self.question.id,
            "title": "API에서 만든 세션",
            "using_model": ChatModel.OPENAI,
        }

        response = self.client.post(self.url, payload, format="json")

        # HTTP status 코드 검증
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        # DB에 ChatbotSession 이 하나 생성됐는지 확인
        self.assertEqual(ChatbotSession.objects.count(), 1)
        session: Any = ChatbotSession.objects.first() # 주의할것
        assert session is not None

        # 생성된 인스턴스 필드값 검증
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.question, self.question)
        self.assertEqual(session.title, payload["title"])
        self.assertEqual(session.using_model, ChatModel.OPENAI)

        # 응답 바디(SessionSerializer 포맷) 검증
        data = response.json()
        self.assertEqual(data["id"], session.id)
        self.assertEqual(data["user"], self.user.id)
        self.assertEqual(data["question"], self.question.id)
        self.assertEqual(data["title"], payload["title"])
        self.assertEqual(data["using_model"], ChatModel.OPENAI)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    # if not 인증 -> 세션 생성 요청 시 401?
    # 인증을 강제함으로써 request.user 에 항상 실제 User 인스턴스가 들어오도록 보장한다.
    def test_session_create_401_when_unauthenticated(self) -> None:
        # 인증 해제
        self.client.force_authenticate(user=None)

        payload: dict[str, Any] = {
            "question": self.question.id,
            "using_model": ChatModel.OPENAI,
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 존재하지 않는 question PK 요청할 때 400 or 404 반환하는가?
    # serializer 레벨에서 400 나올수도, view 레벨에서 404 나올수도.
    def test_session_create_400_when_question_not_exists(self) -> None:
        invalid_question_id = self.question.id + 9999

        payload: dict[str, Any] = {
            "question": invalid_question_id,
            "using_model": ChatModel.OPENAI,
        }

        response = self.client.post(self.url, payload, format="json")

        # 정책에 따라 400 또는 404 중 하나를 기대할 수 있다.
        # 우선 4xx 인지만 검증하고, 필요하면 구체 status로 좁혀도 된다.
        self.assertIn(response.status_code, {status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND})


# 세션 목록 조회 api 테스트
class SessionListAPITests(APITestCase):
    """Session 목록 조회 API 테스트"""

    user: "User"
    other_user: "User"
    question_category: QuestionCategory
    question: Question
    question2: Question
    question3: Question
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create(
            email="test@example.com",
            password="pass",
            name="mainuser",
            nickname="mainuser",
            birthday=datetime.date(2000, 1, 1),
        )

        cls.other_user = User.objects.create(
            email="other@example.com",
            password="pass",
            name="otheruser",
            nickname="otheruser",
            birthday=datetime.date(2000, 1, 1),
        )

        cls.question_category = QuestionCategory.objects.create(name="test_category")

        cls.question = Question.objects.create(
            author=cls.user, title="Q1", content="...", category=cls.question_category
        )
        cls.question2 = Question.objects.create(
            author=cls.other_user, title="Q2", content="...", category=cls.question_category
        )

        # user의 세션 2개
        ChatbotSession.objects.create(user=cls.user, question=cls.question, title="세션1", using_model="gemini")
        ChatbotSession.objects.create(user=cls.user, question=cls.question2, title="세션2", using_model="openai")

        # 다른 유저의 세션 (보이면 안 됨)
        cls.question3 = Question.objects.create(
            author=cls.other_user, title="Q3", content="...", category=cls.question_category
        )

        ChatbotSession.objects.create(
            user=cls.other_user, question=cls.question3, title="남의세션", using_model="gemini"
        )

        cls.url = reverse("aichatbot:session-list-create")

    def setUp(self) -> None:
        self.client.force_authenticate(self.user)

    def test_list_returns_only_own_sessions(self) -> None:
        """✅ 본인 세션만 반환되는지 테스트"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)  # 본인 것만

    def test_list_pagination_works(self) -> None:
        """✅ page_size 파라미터가 작동하는지 테스트"""
        response = self.client.get(self.url, {"page_size": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["next"])  # 다음 페이지 존재

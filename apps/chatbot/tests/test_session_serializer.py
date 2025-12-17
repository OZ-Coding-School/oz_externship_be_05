import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory
from django.test import TestCase

from apps.chatbot.models.chatbot_sessions import ChatbotSession, ChatModel
from apps.chatbot.serializers.session_serializers import SessionCreateSerializer
from apps.qna.models import QuestionCategory
from apps.qna.models.question.question_base import Question
from apps.user.models import User

"""
목표: 유저 생성 - 질문 생성 - 인증 설정 - URL 설정
"""


class SessionCreateSerializerTests(TestCase):
    user: User
    question_category: QuestionCategory
    question: Question
    factory: APIRequestFactory

    @classmethod
    def setUpTestData(cls) -> None:
        UserModel = get_user_model()
        # 유저 생성
        cls.user = UserModel.objects.create(
            email="test@example.com", password="00000000", birthday=datetime.date(2000, 1, 1)
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

        # DRF Request 객체 만들기용
        cls.factory = APIRequestFactory()

        # 실제 HTTP 요청 대신 APIRequestFactory 사용해 가짜 Request를 만들어요

    def _make_request_with_user(self) -> HttpRequest:
        request = self.factory.post("/fake-url", {})
        request.user = self.user
        return request

    # 정상 입력값으로 SessionCreateSerializers → Chatbot_Session 생성하는지 checkckkck
    def test_valid_payload_creates_session(self) -> None:
        data: dict[str, str | int] = {
            "question": self.question.id,
            "title": "test_session",
            "using_model": ChatModel.OPENAI,
        }

        request = self._make_request_with_user()
        serializer = SessionCreateSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        session = serializer.save()

        # DB에 1개가 생성되었나요?
        self.assertEqual(ChatbotSession.objects.count(), 1)

        self.assertEqual(session.user, self.user)
        self.assertEqual(session.question, self.question)
        self.assertEqual(session.title, data["title"])
        self.assertEqual(session.using_model, ChatModel.OPENAI)

    # 사용모델 누락 시 serializer가 에러메세지 반환하는지 테스트
    def test_missing_using_model_is_valid(self) -> None:
        data: dict[str, Any] = {
            "question": self.question.id,
        }

        request = self._make_request_with_user()
        serializer = SessionCreateSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        # 에러: dict에 using_model키가 존재해야 함.
        self.assertIn("using_model", serializer.errors)

    # choice에 없는 모델 보냈을때 invalid 테스트
    def test_invalid_using_model_choice_is_invalid(self) -> None:
        data: dict[str, Any] = {
            "question": self.question,
            "using_model": "fakeAI",
        }

        request = self._make_request_with_user()
        serializer = SessionCreateSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("using_model", serializer.errors)

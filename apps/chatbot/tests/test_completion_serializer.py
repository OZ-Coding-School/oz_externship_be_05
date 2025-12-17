from typing import Any
from django.http import HttpRequest
from django.test import TestCase
from rest_framework.test import APIRequestFactory
import datetime

from apps.chatbot.models.chatbot_completions import ChatbotCompletion
from apps.chatbot.models.chatbot_sessions import ChatbotSession, ChatModel
from apps.chatbot.serializers.completion_serializers import CompletionCreateSerializer
from apps.qna.models.question.question_category import QuestionCategory
from apps.qna.models.question.question_base import Question
from apps.user.models.user import User


class CompletionCreateSerializerTests(TestCase):
    user: User
    password: str
    question_category: QuestionCategory
    question: Question
    session: ChatbotSession

    # 데이터 생성
    @classmethod
    def setUpTestData(cls) -> None:
        cls.password = "00000000"
        cls.user = User.objects.create_user(
            email="test@example.com",
            password=cls.password,
            name="testuser",
            nickname="testuser",
            birthday=datetime.date(2000, 1, 1),
        )

        cls.question_category = QuestionCategory.objects.create(
            name="testcategory",
        )

        cls.question = Question.objects.create(
            author=cls.user,
            category=cls.question_category,
            title="test_title",
            content="test_content",
        )

        cls.session = ChatbotSession.objects.create(
            user=cls.user,
            question=cls.question,
            title="test_title",
            using_model=ChatModel.OPENAI,
        )

        cls.factory = APIRequestFactory()

    # 리퀘스트 생성
    def _make_request(self) -> HttpRequest:
        request = self.factory.post("/fake-url", {})
        request.user = self.user
        return request

    # 정상 입력 → 시리얼라이저 통해 create → chatbotcompletion 생성?
    def test_valid_payload_create_completion(self) -> None:
        data: dict[str, str] = {
            "message": "AI에게 질문.",
        }

        request = self._make_request()
        serializer = CompletionCreateSerializer(
            data=data,
            context={"request": request, "session": self.session},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        completion = serializer.save()

        # DB에 세션 1개만 생성됐나요?
        self.assertEqual(ChatbotCompletion.objects.count(), 1)
        self.assertEqual(completion.session, self.session)
        self.assertEqual(completion.message, data["message"])
        self.assertEqual(completion.role, "user")


    # 메세지 누락 케이스

    # 빈 메세지면 invalid 나오나요(경우가 더 있나 이거)

    #
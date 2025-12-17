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
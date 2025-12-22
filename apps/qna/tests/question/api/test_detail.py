from django.urls import reverse
from rest_framework.test import APITestCase

from apps.core.exceptions.exception_messages import EMS
from apps.qna.models import (
    Answer,
    AnswerComment,
    Question,
    QuestionCategory,
)
from apps.user.models import User
from apps.user.models.user import RoleChoices


class QuestionDetailAPITests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="apitest@test.com",
            password="test1234",
            name="유저",
            role=RoleChoices.ST,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
        )

        self.answer_user = User.objects.create_user(
            email="answer@test.com",
            password="test1234",
            name="답변유저",
            role=RoleChoices.ST,
            phone_number="010-1111-1111",
            gender="M",
            birthday="1999-01-01",
        )

        self.category = QuestionCategory.objects.create(name="Django")

        self.question = Question.objects.create(
            author=self.user,
            title="질문 제목",
            content="질문 내용",
            category=self.category,
        )

        self.answer = Answer.objects.create(
            question=self.question,
            author=self.answer_user,
            content="답변 내용",
            is_adopted=False,
        )

        self.comment = AnswerComment.objects.create(
            answer=self.answer,
            author=self.user,
            content="댓글 내용",
        )

        self.url = reverse("question_detail", kwargs={"question_id": self.question.id})

    def test_question_detail_with_answers_and_comments(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        data = response.data

        # 질문 기본 필드
        self.assertEqual(data["id"], self.question.id)
        self.assertEqual(data["title"], "질문 제목")
        self.assertEqual(data["content"], "질문 내용")

        # author
        self.assertEqual(data["author"]["nickname"], self.user.nickname)

        # answers
        self.assertEqual(len(data["answers"]), 1)

        answer_data = data["answers"][0]
        self.assertEqual(answer_data["content"], "답변 내용")
        self.assertFalse(answer_data["is_adopted"])
        self.assertEqual(
            answer_data["author"]["nickname"],
            self.answer_user.nickname,
        )

        # comments
        self.assertEqual(len(answer_data["comments"]), 1)

        comment_data = answer_data["comments"][0]
        self.assertEqual(comment_data["content"], "댓글 내용")
        self.assertEqual(
            comment_data["author"]["nickname"],
            self.user.nickname,
        )

    def test_invalid_question_id(self) -> None:
        url = reverse("question_detail", args=[0])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error_detail"],
            EMS.E400_INVALID_REQUEST("질문 상세 조회")["error_detail"],
        )

from django.urls import reverse
from rest_framework import status

from apps.qna.models.answer.answers import Answer
from apps.qna.models.question import Question
from apps.qna.tests.answer.views.test_answer_view_base import _AnswerViewDBBase


class TestAnswerDetailAPIView(_AnswerViewDBBase):
    def setUp(self) -> None:
        super().setUp()
        self.answer = Answer.objects.create(author=self.user, question=self.question, content="테스트 답변 내용")
        self.other_question = Question.objects.create(
            author=self.user, category=self.question_category, title="관계 없는 질문", content="내용"
        )

    def get_url(self, question_id: int, pk: int) -> str:
        return reverse("answers:answer_detail", kwargs={"question_id": question_id, "pk": pk})

    def test_get_answer_detail_success(self) -> None:
        url = self.get_url(self.question.id, self.answer.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.answer.id)

    def test_get_answer_detail_mismatch_404(self) -> None:
        url = self.get_url(self.other_question.id, self.answer.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_answer_success(self) -> None:
        url = self.get_url(self.question.id, self.answer.id)
        data = {"content": "수정된 답변 내용"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.content, "수정된 답변 내용")

    def test_put_answer_mismatch_404(self) -> None:
        url = self.get_url(self.other_question.id, self.answer.id)
        data = {"content": "수정 시도"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_answer_non_owner_forbidden(self) -> None:
        self.client.force_authenticate(user=self.other_user)
        url = self.get_url(self.question.id, self.answer.id)
        response = self.client.put(url, {"content": "타인 수정"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_answer_success(self) -> None:
        url = self.get_url(self.question.id, self.answer.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Answer.objects.filter(id=self.answer.id).exists())

    def test_delete_answer_mismatch_404(self) -> None:
        url = self.get_url(self.other_question.id, self.answer.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Answer.objects.filter(id=self.answer.id).exists())

    def test_delete_answer_non_owner_forbidden(self) -> None:
        self.client.force_authenticate(user=self.other_user)
        url = self.get_url(self.question.id, self.answer.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

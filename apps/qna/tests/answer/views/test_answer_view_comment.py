from django.urls import reverse
from rest_framework import status

from apps.qna.models.answer.answers import Answer
from apps.qna.models.answer.comments import AnswerComment
from apps.qna.tests.answer.views.test_answer_view_base import _AnswerViewDBBase


class TestCommentAPIView(_AnswerViewDBBase):
    def setUp(self) -> None:
        super().setUp()
        self.test_answer = Answer.objects.create(author=self.user, question=self.question, content="Test Answer")
        self.list_url = reverse(
            "answers:comment_list", kwargs={"question_id": self.question.id, "answer_id": self.test_answer.id}
        )

    def test_create_comment_success(self) -> None:
        """댓글 생성 성공 및 응답 데이터 검증"""
        data = {"content": "새로운 댓글입니다."}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("comment_id", response.data)

    def test_get_comment_list_pagination(self) -> None:
        """댓글 목록 페이징 작동 확인"""
        # 11개의 댓글 생성 (page_size=10)
        for i in range(11):
            AnswerComment.objects.create(author=self.user, answer=self.test_answer, content=f"댓글 {i}")

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next", response.data)  # 커서 페이징 확인
        self.assertEqual(len(response.data["results"]), 10)

    def test_update_comment_success(self) -> None:
        """댓글 수정 성공"""
        comment = AnswerComment.objects.create(author=self.user, answer=self.test_answer, content="원본 댓글")
        url = reverse(
            "answers:comment_detail",
            kwargs={"question_id": self.question.id, "answer_id": self.test_answer.id, "pk": comment.id},
        )

        response = self.client.put(url, {"content": "수정된 댓글"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.content, "수정된 댓글")

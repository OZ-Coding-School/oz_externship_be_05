from django.urls import reverse
from rest_framework import status

from apps.qna.models.answer.answers import Answer
from apps.qna.tests.answer.views.test_answer_view_base import _AnswerViewDBBase

"""
Answer Views 테스트
- AnswerListAPIView (GET, POST)
"""


class TestAnswerListAPIView(_AnswerViewDBBase):
    def get_url(self, question_id: int) -> str:
        return reverse("answers:answer_list", kwargs={"question_id": question_id})

    # ----- GET Tests -----

    def test_get_answer_list_success(self) -> None:
        """답변 목록 조회 성공"""
        Answer.objects.create(
            author=self.user,
            question=self.question,
            content="답변 1",
        )
        Answer.objects.create(
            author=self.other_user,
            question=self.question,
            content="답변 2",
        )

        response = self.client.get(self.get_url(self.question.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_answer_list_empty(self) -> None:
        """답변이 없는 경우 빈 리스트 반환"""
        response = self.client.get(self.get_url(self.question.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_get_answer_list_ordered_by_created_at_desc(self) -> None:
        """최신순 정렬 확인"""
        answer1 = Answer.objects.create(
            author=self.user,
            question=self.question,
            content="먼저 작성",
        )
        answer2 = Answer.objects.create(
            author=self.user,
            question=self.question,
            content="나중에 작성",
        )

        response = self.client.get(self.get_url(self.question.id))

        self.assertEqual(response.data[0]["id"], answer2.id)
        self.assertEqual(response.data[1]["id"], answer1.id)

    def test_get_answer_list_unauthenticated_denied(self) -> None:
        """✅ 비인증 유저는 접근 불가"""
        self.client.force_authenticate(user=None)

        response = self.client.get(self.get_url(self.question.id))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---- POST ---- #

    def test_post_answer_success(self) -> None:
        """✅ 답변 생성 성공"""
        data = {"content": "새로운 답변입니다."}

        response = self.client.post(self.get_url(self.question.id), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("answer_id", response.data)
        self.assertEqual(Answer.objects.count(), 1)

    def test_post_answer_invalid_content(self) -> None:
        """✅ 빈 content로 생성 시 400"""
        data = {"content": ""}

        response = self.client.post(self.get_url(self.question.id), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_answer_invalid_question_id(self) -> None:
        """✅ 존재하지 않는 질문 ID로 생성 시 404"""
        data = {"content": "답변 내용"}

        response = self.client.post(self.get_url(99999), data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

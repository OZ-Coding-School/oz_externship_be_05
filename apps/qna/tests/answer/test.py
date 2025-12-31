from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.qna.models.answer.answers import Answer
from apps.qna.models.question import Question
from apps.user.models.user import RoleChoices

User = get_user_model()


class AnswerViewTestCase(APITestCase):
    def setUp(self) -> None:
        # 1. 수강생
        self.student = User.objects.create_user(
            email="student@test.com",
            password="password",
            name="학생",
            role=RoleChoices.ST,
            birthday="2000-01-01",
            gender="M",
            phone_number="010-1111-1111",
        )

        # 2. 튜터
        self.tutor = User.objects.create_user(
            email="tutor@test.com",
            password="password",
            name="튜터",
            role=RoleChoices.TA,
            birthday="1990-01-01",
            gender="F",
            phone_number="010-2222-2222",
        )

        # 3. 일반 유저
        self.normal_user = User.objects.create_user(
            email="user@test.com",
            password="password",
            name="일반유저",
            role=RoleChoices.USER,
            birthday="2000-05-05",
            gender="M",
            phone_number="010-3333-3333",
        )

        # 4. 질문자
        self.questioner = User.objects.create_user(
            email="questioner@test.com",
            password="password",
            name="질문자",
            role=RoleChoices.ST,
            birthday="2001-01-01",
            gender="F",
            phone_number="010-4444-4444",
        )

        # 질문 및 답변 기본 데이터
        self.question = Question.objects.create(
            author=self.questioner,
            title="테스트 질문",
            content="질문 내용입니다.",
        )
        self.answer = Answer.objects.create(
            question=self.question,
            author=self.student,
            content="기존 답변입니다.",
        )

        base_prefix = "/api/qna"

        # API 엔드포인트
        self.list_create_url = f"{base_prefix}/questions/{self.question.id}/answers/"
        self.detail_url = f"{base_prefix}/questions/{self.question.id}/answers/{self.answer.id}/"
        self.adopt_url = f"{base_prefix}/questions/{self.question.id}/answers/{self.answer.id}/adopt/"

    # ---------- Answer 생성 ----------

    def test_create_answer_success(self) -> None:
        """허용된 Role(ST)은 답변을 생성할 수 있다."""
        self.client.force_authenticate(user=self.student)

        response = self.client.post(
            self.list_create_url,
            {"question_id": self.question.id, "content": "새로운 답변입니다."},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Answer.objects.count(), 2)

    def test_create_answer_fail_role(self) -> None:
        """허용되지 않은 Role(USER)는 답변을 생성할 수 없다."""
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.post(
            self.list_create_url,
            {"question_id": self.question.id, "content": "권한 없는 요청"},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------- Answer 수정 / 삭제 ----------

    def test_update_answer_success(self) -> None:
        """답변 작성자는 자신의 답변을 수정할 수 있다."""
        self.client.force_authenticate(user=self.student)

        response = self.client.put(
            self.detail_url,
            {"content": "수정된 답변"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.content, "수정된 답변")

    def test_update_answer_fail_not_owner(self) -> None:
        """작성자가 아닌 사용자는 답변을 수정할 수 없다."""
        self.client.force_authenticate(user=self.tutor)

        response = self.client.put(
            self.detail_url,
            {"content": "권한 없는 수정 시도"},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_answer_success(self) -> None:
        """답변 작성자는 자신의 답변을 삭제할 수 있다."""
        self.client.force_authenticate(user=self.student)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Answer.objects.filter(id=self.answer.id).exists())

    # ---------- Answer 채택 ----------

    def test_adopt_answer_success(self) -> None:
        """질문 작성자는 답변을 채택할 수 있다."""
        self.client.force_authenticate(user=self.questioner)

        response = self.client.post(self.adopt_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.answer.refresh_from_db()
        self.assertTrue(self.answer.is_adopted)

    def test_adopt_answer_fail_not_question_owner(self) -> None:
        """질문 작성자가 아니면 답변을 채택할 수 없다."""
        self.client.force_authenticate(user=self.student)

        response = self.client.post(self.adopt_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_adopt_answer_toggle(self) -> None:
        """이미 채택된 답변은 다시 요청 시 채택이 취소된다."""
        self.answer.is_adopted = True
        self.answer.save()

        self.client.force_authenticate(user=self.questioner)
        response = self.client.post(self.adopt_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.answer.refresh_from_db()
        self.assertFalse(self.answer.is_adopted)

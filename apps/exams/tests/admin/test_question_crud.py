from typing import Any, ClassVar

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Course, Subject
from apps.exams.models import Exam, ExamQuestion


class ExamAdminQuestionViewTest(APITestCase):
    """관리자용 쪽지시험 문제(Question) CRUD 테스트"""

    course: ClassVar[Course]
    admin_user: ClassVar[Any]
    subject: ClassVar[Subject]
    exam: ClassVar[Exam]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.course = Course.objects.create(name="QA 코스")
        cls.admin_user = get_user_model().objects.create_superuser(
            email="admin_q@test.com", password="testpassword", name="admin_q", birthday="1990-01-01"
        )
        cls.subject = Subject.objects.create(
            title="테스트 과목", course=cls.course, number_of_days=10, number_of_hours=10
        )
        cls.exam = Exam.objects.create(title="기본 시험", subject=cls.subject)

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        # 기본 문제 생성 (options_json -> options 필드명 수정 반영)
        self.question_a = ExamQuestion.objects.create(
            exam=self.exam,
            type="multiple_choice",
            question="기존 문제",
            options=["1", "2"],
            answer=["1"],
            point=10,
            explanation="기본 해설",
        )

        self.detail_url = reverse("exam-questions-detail", kwargs={"question_id": self.question_a.id})

    def test_update_question_success(self) -> None:
        """문제 수정 성공 테스트"""
        data = {"question": "수정된 질문 내용", "point": 7, "explanation": "해설 수정"}
        response = self.client.put(self.detail_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.question_a.refresh_from_db()
        self.assertEqual(self.question_a.question, "수정된 질문 내용")
        self.assertEqual(self.question_a.point, 7)

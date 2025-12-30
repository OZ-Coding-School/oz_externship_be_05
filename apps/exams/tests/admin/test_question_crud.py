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

        self.create_url = reverse("exam-questions", kwargs={"exam_id": self.exam.id})
        self.detail_url = reverse("exam-questions-detail", kwargs={"question_id": self.question_a.id})

    def test_create_question_success(self) -> None:
        """문제 생성 성공 테스트 (multiple_choice)"""
        data = {
            "type": "multiple_choice",
            "question": "새로운 객관식 문제",
            "options": ["A", "B", "C"],
            "correct_answer": ["A"],
            "point": 5,
            "explanation": "신규 해설",
            "blank_count": 0,
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExamQuestion.objects.count(), 2)

    def test_create_all_types_success(self) -> None:
        """제공된 모든 문제 유형(6종) 생성 성공 테스트"""
        types_to_test = [
            ("single_choice", ["A", "B"], ["A"]),
            ("multiple_choice", ["A", "B"], ["A", "B"]),
            ("ox", ["O", "X"], ["O"]),
            ("short_answer", None, ["답안"]),
            ("ordering", ["1", "2"], ["1", "2"]),
            ("fill_blank", None, ["빈칸"]),
        ]

        for q_type, options, answer in types_to_test:
            data = {
                "type": q_type,
                "question": f"{q_type} 테스트",
                "options": options,
                "correct_answer": answer,
                "point": 1,
                "explanation": "해설",
            }
            response = self.client.post(self.create_url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed on type: {q_type}")

    def test_create_question_explanation_empty_success(self) -> None:
        """explanation이 null로 들어와도 저장되는지 확인"""
        data = {
            "type": "ox",
            "question": "O/X 문제",
            "correct_answer": ["O"],
            "point": 5,
            "explanation": "",
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_q = ExamQuestion.objects.get(question="O/X 문제")
        # DB 필드 설정에 따라 "" 혹은 None으로 검증
        self.assertTrue(new_q.explanation == "" or new_q.explanation is None)

    def test_create_question_missing_explanation_success(self) -> None:
        """explanation 키 누락 시 성공"""
        data = {
            "type": "ox",
            "question": "키 누락 테스트",
            "correct_answer": ["O"],
            "point": 5,
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_question_point_limit_fails(self) -> None:
        """총 배점 초과 시 실패 (EMS 메시지 인자 수정 반영)"""
        data = {
            "type": "multiple_choice",
            "question": "고배점 문제",
            "correct_answer": ["1"],
            "point": 91,  # 기존 10 + 91 = 101 (100 초과)
            "explanation": "해설",
        }
        response = self.client.post(self.create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 에러 디테일 메시지가 존재하는지 확인
        self.assertIn("error_detail", response.data)

    def test_create_question_count_limit_fails(self) -> None:
        """문제 수 20개 초과 시 생성 실패"""
        # 19개 추가 생성 (기본 1개 포함 총 20개) - type을 "ox_quiz"에서 "ox"로 수정
        for i in range(19):
            ExamQuestion.objects.create(
                exam=self.exam, type="ox", question=f"Q{i}", answer=["O"], point=1, explanation=""
            )

        data = {"type": "ox", "question": "21번째", "correct_answer": ["O"], "point": 1, "explanation": ""}
        response = self.client.post(self.create_url, data, format="json")
        print(ExamQuestion.objects.count())
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_update_question_success(self) -> None:
        """문제 수정 성공 테스트 PATCH """
        data = {"question": "수정된 질문 내용", "point": 7, "explanation": "해설 수정"}
        response = self.client.patch(self.detail_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.question_a.refresh_from_db()
        self.assertEqual(self.question_a.question, "수정된 질문 내용")
        self.assertEqual(self.question_a.point, 7)

    def test_delete_question_success(self) -> None:
        """문제 삭제 성공 테스트"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ExamQuestion.objects.count(), 0)

    def test_delete_non_existent_question_fails(self) -> None:
        """존재하지 않는 문제 삭제 시 404 확인"""
        url = reverse("exam-questions-detail", kwargs={"question_id": 9999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

from datetime import date, datetime, timedelta
from typing import Any

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models.exam import Exam
from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.models.exam_question import ExamQuestion, QuestionType
from apps.exams.models.exam_submission import ExamSubmission
from apps.user.models import User


class SimpleExamSubmitTest(TestCase):
    def setUp(self) -> None:
        # 유저 생성
        self.user = User.objects.create_user(
            email="test@example.com",
            name="테스트",
            password="1234",
            birthday=date(2000, 5, 18),
        )

        # DRF APIClient + 인증 강제
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # 코스
        self.course = Course.objects.create(
            name="course",
            tag="TT",
            description="test course description",
        )

        # 코호트
        self.cohort = Cohort.objects.create(
            course=self.course,
            number=1,
            max_student=20,
            start_date=timezone.make_aware(datetime(2025, 1, 1)),
            end_date=timezone.make_aware(datetime(2025, 2, 1)),
        )

        # 과목
        self.subject = Subject.objects.create(
            course=self.course,
            title="test subject",
            number_of_days=1,
            number_of_hours=1,
        )

        # 시험
        self.exam = Exam.objects.create(
            title="test exam",
            subject=self.subject,
        )

        # ---------- 공주의 규칙 문제 세트 ----------

        # 1) 단일 선택
        self.single_choice_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주가 아침에 가장 먼저 해야 하는 일은 무엇일까요?",
            type=QuestionType.SINGLE_CHOICE,
            options=["울기", "세수하기", "미소 짓기", "왕자를 찾기"],
            answer="3",
            point=5,
        )

        # 2) 다중 선택
        self.multiple_choice_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주가 하루 동안 반드시 해야 하는 두 가지 규칙은?",
            type=QuestionType.MULTIPLE_CHOICE,
            options=["감사 인사하기", "하루 종일 잠자기", "화내지 않기", "친구에게 칭찬하기"],
            answer=["1", "4"],
            point=10,
        )

        # 3) OX
        self.ox_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주가 배가 고프면 무조건 울어야 한다. (O/X)",
            type=QuestionType.OX,
            answer="X",
            point=3,
        )

        # 4) 단답형
        self.short_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주의 규칙 1번은 무엇인가요?",
            type=QuestionType.SHORT_ANSWER,
            answer="울지않기",
            point=5,
        )

        # 5) 순서 정렬
        self.ordering_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주의 아침 루틴을 순서대로 나열하세요.",
            type=QuestionType.ORDERING,
            options=["A", "B", "C", "D"],
            answer=["A", "B", "C", "D"],
            point=7,
        )

        # 6) 빈칸 채우기
        self.fill_blank_question = ExamQuestion.objects.create(
            exam=self.exam,
            question='공주의 좌우명을 완성하세요: "_____, 그리고 _____."',
            type=QuestionType.FILL_BLANK,
            blank_count=2,
            answer=["용기", "친절"],
            point=8,
        )

        # 스냅샷 생성
        questions = [
            self.single_choice_question,
            self.multiple_choice_question,
            self.ox_question,
            self.short_question,
            self.ordering_question,
            self.fill_blank_question,
        ]

        self.deployment = ExamDeployment.objects.create(
            exam=self.exam,
            cohort=self.cohort,
            duration_time=60,
            open_at=timezone.now(),
            close_at=timezone.now() + timedelta(hours=1),
            questions_snapshot={
                "questions": [
                    {
                        "question_id": q.id,
                        "question": q.question,
                        "type": q.type,
                        "answer": q.answer,
                        "point": q.point,
                    }
                    for q in questions
                ]
            },
        )

        # URL
        self.url = reverse(
            "exam_submit",
            kwargs={"deployment_pk": self.deployment.pk},
        )

    def test_submit_success(self) -> None:
        """6문항 모두 정답을 제출하면 score=38, correct_count=6이어야 한다."""
        payload = {
            "started_at": (timezone.now() - timedelta(seconds=10)).isoformat(),
            "cheating_count": 0,
            "answers": {
                "questions": [
                    {"question_id": self.single_choice_question.id, "answer": "3"},
                    {"question_id": self.multiple_choice_question.id, "answer": ["1", "4"]},
                    {"question_id": self.ox_question.id, "answer": "X"},
                    {"question_id": self.short_question.id, "answer": "울지않기"},
                    {"question_id": self.ordering_question.id, "answer": ["A", "B", "C", "D"]},
                    {"question_id": self.fill_blank_question.id, "answer": ["용기", "친절"]},
                ]
            },
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201)

        submission = ExamSubmission.objects.get()
        self.assertEqual(submission.score, 38)
        self.assertEqual(submission.correct_answer_count, 6)

    def make_payload(self) -> dict[str, Any]:
        """단답형만 포함된 기본 payload"""
        return {
            "started_at": (timezone.now() - timedelta(seconds=10)).isoformat(),
            "cheating_count": 0,
            "answers": {
                "questions": [
                    {"question_id": self.short_question.id, "answer": "울지않기"},
                ]
            },
        }

    def test_submit_success_once(self) -> None:
        """단답형 1개만 제출하면 score=5, correct=1"""
        payload = self.make_payload()
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 201)

        submission = ExamSubmission.objects.get()
        self.assertEqual(submission.score, 5)
        self.assertEqual(submission.correct_answer_count, 1)

    def test_submit_fail_third(self) -> None:
        """같은 시험은 최대 2회까지 제출 가능 → 3번째는 400"""
        payload = self.make_payload()

        # 1회차 성공
        first = self.client.post(self.url, payload, format="json")
        self.assertEqual(first.status_code, 201)

        # 2회차 성공
        second = self.client.post(self.url, payload, format="json")
        self.assertEqual(second.status_code, 201)

        # 3회차 → 실패
        third = self.client.post(self.url, payload, format="json")
        self.assertEqual(third.status_code, 400)

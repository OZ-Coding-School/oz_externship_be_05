from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date, datetime

from rest_framework.test import APIClient

from apps.user.models import User
from apps.courses.models import Subject, Course, Cohort
from apps.exams.models.exam import Exam
from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.models.exam_question import ExamQuestion, QuestionType
from apps.exams.models.exam_submission import ExamSubmission


class SimpleExamSubmitTest(TestCase):
    def setUp(self) -> None:
        # 유저 생성
        self.user = User.objects.create_user(
            email="test@example.com",
            name="테스트",
            password="1234",
            birthday=date(2000, 5, 18),
        )

        # DRF APIClient 사용 + 인증 강제
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

        # 문제 1개 생성
        self.question = ExamQuestion.objects.create(
            exam=self.exam,
            question="파이썬의 철자?",
            type=QuestionType.SHORT_ANSWER,
            answer="파이썬",
            point=5,
        )

        # 시험 배포
        self.deployment = ExamDeployment.objects.create(
            exam=self.exam,
            cohort=self.cohort,
            duration_time=60,
            open_at=timezone.now(),
            close_at=timezone.now() + timedelta(hours=1),
            questions_snapshot={
                "questions": [
                    {
                        "question_id": self.question.id,
                        "question": self.question.question,
                        "type": self.question.type,
                        "answer": self.question.answer,
                        "point": self.question.point,
                    }
                ]
            },
        )

        # URL
        self.url = reverse(
            "exam_submit",
            kwargs={"deployment_pk": self.deployment.pk},
        )

    def test_submit_success(self) -> None:
        """정상적으로 제출이 1회 성공하는지"""
        payload = {
            "started_at": (timezone.now() - timedelta(seconds=10)).isoformat(),
            "cheating_count": 0,
            "answers": {
                "questions": [
                    {"question_id": self.question.id, "answer": "파이썬"}
                ]
            },
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201)

        submission = ExamSubmission.objects.get()
        self.assertEqual(submission.score, 5)
        self.assertEqual(submission.correct_answer_count, 1)

    def test_submit_twice_fail(self) -> None:
        """같은 유저가 같은 시험을 2번 제출하면 실패해야 함"""
        payload = {
            "started_at": (timezone.now() - timedelta(seconds=10)).isoformat(),
            "cheating_count": 0,
            "answers": {
                "questions": [
                    {"question_id": self.question.id, "answer": "파이썬"}
                ]
            },
        }

        # 첫 번째 제출 (성공)
        first = self.client.post(self.url, payload, format="json")
        self.assertEqual(first.status_code, 201)

        # 두 번째 제출 (실패)
        second = self.client.post(self.url, payload, format="json")
        self.assertEqual(second.status_code, 400)

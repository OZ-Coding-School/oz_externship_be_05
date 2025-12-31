from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models import Exam, ExamDeployment, ExamSubmission
from apps.exams.models.exam_question import QuestionType
from apps.user.models.user import GenderChoices, RoleChoices, User


class ExamSubmissionCreateAPIViewIntegrationTestCase(APITestCase):
    """
    쪽지시험 제출 API 통합 테스트
    """

    student: User
    deployment: ExamDeployment
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.student = User.objects.create_user(
            email="student@test.com",
            password="password123",
            name="학생",
            gender=GenderChoices.MALE,
            birthday=timezone.now(),
            role=RoleChoices.ST,
        )

        course = Course.objects.create(name="코스")
        cohort = Cohort.objects.create(
            course=course,
            number=1,
            max_student=20,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
        )
        subject = Subject.objects.create(
            course=course,
            title="과목",
            number_of_days=1,
            number_of_hours=1,
        )
        exam = Exam.objects.create(
            subject=subject,
            title="쪽지시험",
        )

        cls.deployment = ExamDeployment.objects.create(
            exam=exam,
            cohort=cohort,
            open_at=timezone.now() - timedelta(minutes=30),
            close_at=timezone.now() + timedelta(minutes=30),
            duration_time=600,
            questions_snapshot=[
                {
                    "id": 1,
                    "type": QuestionType.SINGLE_CHOICE,
                    "answer": "A",
                    "point": 10,
                },
                {
                    "id": 2,
                    "type": QuestionType.OX,
                    "answer": "O",
                    "point": 10,
                },
            ],
        )

        cls.url = reverse(
            "exam_submit",
        )

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.student)

        self.valid_payload = {
            "deployment": self.deployment.id,
            "started_at": (timezone.now() - timedelta(minutes=3)).isoformat(),
            "cheating_count": 0,
            "answers": [
                {
                    "question_id": 1,
                    "submitted_answer": ["A"],
                },
                {
                    "question_id": 2,
                    "submitted_answer": ["O"],
                },
            ],
        }

    def test_submit_exam_success_full_flow(self) -> None:
        """
        정상 제출 시
        - serializer.validate 통과
        - service 채점 수행
        - ExamSubmission 생성
        - 점수 / 정답 수 반환
        """
        response = self.client.post(self.url, data=self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        pk = response["Location"].split("/")[-1]
        submission = ExamSubmission.objects.get(pk=pk)
        self.assertEqual(submission.score, 20)
        self.assertEqual(submission.correct_answer_count, 2)
        self.assertEqual(len(submission.answers), 2)

    def test_submit_exam_started_at_in_future(self) -> None:
        """
        started_at 이 미래인 경우 serializer.validate 에서 400
        """
        payload = self.valid_payload | {
            "started_at": (timezone.now() + timedelta(minutes=1)).isoformat(),
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_exam_time_limit_exceeded(self) -> None:
        """
        시험 제한 시간 초과 serializer.validate 에서 400
        """
        payload = self.valid_payload | {
            "started_at": (timezone.now() - timedelta(minutes=20)).isoformat(),
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_exam_conflict_third_submission(self) -> None:
        """
        제출 2회 초과 → validate_exam_submission_limit 409
        """
        # 2회 제출
        self.client.post(self.url, data=self.valid_payload, format="json")
        self.client.post(self.url, data=self.valid_payload, format="json")

        # 3회 제출
        response = self.client.post(self.url, data=self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models import Exam, ExamDeployment
from apps.exams.models.exam_submission import ExamSubmission
from apps.user.models.user import GenderChoices, User


class ExamAdminSubmissionDetailViewTestCase(APITestCase):

    admin_user: User
    student_user: User
    unauthorized_user: User
    course: Course
    subject: Subject
    cohort: Cohort
    exam: Exam
    deployment: ExamDeployment
    submission: ExamSubmission

    @classmethod
    def setUpTestData(cls) -> None:
        """테스트 데이터 설정"""
        # Users
        cls.admin_user = User.objects.create_superuser(
            email="admin@test.com",
            password="password123",
            name="관리자",
            phone_number="010-1234-5678",
            gender=GenderChoices.MALE,
            birthday=date.today() - timedelta(days=10000),
        )

        cls.student_user = User.objects.create_user(
            email="student@test.com",
            password="password123",
            name="학생",
            phone_number="010-2345-6789",
            gender=GenderChoices.FEMALE,
            birthday=date.today() - timedelta(days=8000),
        )

        cls.unauthorized_user = User.objects.create_user(
            email="user@test.com",
            password="password123",
            name="일반유저",
            phone_number="010-3456-7890",
            gender=GenderChoices.MALE,
            birthday=date.today() - timedelta(days=9000),
        )

        # Course / Subject / Cohort / Exam / Deployment
        cls.course = Course.objects.create(name="테스트")
        cls.subject = Subject.objects.create(
            title="나",
            course=cls.course,
            number_of_days=10,
            number_of_hours=20,
        )
        cls.cohort = Cohort.objects.create(
            number=1,
            course=cls.course,
            max_student=30,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        cls.exam = Exam.objects.create(
            subject=cls.subject,
            title="중간고사",
        )

        now = timezone.now()
        cls.deployment = ExamDeployment.objects.create(
            exam=cls.exam,
            cohort=cls.cohort,
            duration_time=60,
            open_at=now - timedelta(hours=2),
            close_at=now + timedelta(hours=2),
            questions_snapshot=[
                {
                    "id": 1,
                    "type": "multiple_choice",
                    "question": "다음 중 지금 내 심정을 모두 고르시오",
                    "prompt": None,
                    "options": ["햎삐", "아자스", "화나쓰", "멍~"],
                    "answer": ["멍~"],
                    "point": 10,
                    "explanation": "잠을 못 자서 머리가 멍해요",
                },
                {
                    "id": 2,
                    "type": "multiple_choice",
                    "question": "곧 있을 휴가 날짜를 맞춰보세요",
                    "prompt": None,
                    "options": ["12/31", "1/2", "1/5", "1/6"],
                    "answer": ["12/31", "1/2"],
                    "point": 15,
                    "explanation": "연말과 연초 모두 쉬는 마법",
                },
                {
                    "id": 3,
                    "type": "short_answer",
                    "question": "내가 좋아하는 숫자는?",
                    "prompt": "0 이상의 정수 중에 있습니다.",
                    "options": None,
                    "answer": ["0"],
                    "point": 20,
                    "explanation": "0이 숫자 뒤에 붙으면 자릿수가 계속 커진닿 ㅔ헤",
                },
            ],
        )

        # ExamSubmission
        cls.submission = ExamSubmission.objects.create(
            deployment=cls.deployment,
            submitter=cls.student_user,
            started_at=now - timedelta(minutes=30),
            created_at=now,
            answers=[
                {"id": 1, "submitted_answer": ["멍~"], "is_correct": True},
                {"id": 2, "submitted_answer": ["12/31", "1/2"], "is_correct": True},
                {"id": 3, "submitted_answer": ["0"], "is_correct": True},
            ],
            score=45,
            correct_answer_count=3,
            cheating_count=0,
        )

    def _get_detail_url(self, submission_id: int) -> str:
        return reverse("exam_submission_detail", kwargs={"submission_id": submission_id})

    def test_get_submission_detail_success(self) -> None:
        """
        응시 내역 상세 조회 성공 및 기본 응답 구조 확인
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self._get_detail_url(self.submission.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 1. 최상위 구조 확인
        self.assertEqual(set(response.data.keys()), {"exam", "student", "result", "questions"})

        # 2. 결과 정보 검증
        result = response.data["result"]
        self.assertEqual(result["total_question_count"], 3)

    def test_questions_merge_logic(self) -> None:
        """Snapshot과 가공된 answers가 잘 병합되었는지 확인"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self._get_detail_url(self.submission.id))

        questions = response.data["questions"]
        q1 = questions[0]

        self.assertEqual(q1["id"], 1)
        self.assertEqual(q1["number"], 1)
        self.assertEqual(q1["submitted_answer"], ["멍~"])
        self.assertEqual(q1["answer"], ["멍~"])
        self.assertTrue(q1["is_correct"])

    def test_get_submission_detail_not_found(self) -> None:
        """404 예외 처리 확인"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self._get_detail_url(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthorized_and_forbidden(self) -> None:
        """권한 체크 확인"""
        url = self._get_detail_url(self.submission.id)

        # 401 Unauthorized
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 403 Forbidden
        unauth_user = User.objects.create_user(email="un@test.com", password="p", name="포비든", birthday=date.today())
        self.client.force_authenticate(user=unauth_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

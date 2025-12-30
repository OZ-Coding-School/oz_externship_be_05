from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.exceptions.exception_messages import EMS
from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course
from apps.courses.models.subjects_models import Subject
from apps.exams.models.exam import Exam
from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.models.exam_submission import ExamSubmission
from apps.user.models.user import RoleChoices, User


class ExamCheatingCheckViewTest(TestCase):
    """
    쪽지시험 부정행위 체크 API 테스트
    """

    student: User
    instructor: User
    course: Course
    cohort: Cohort
    subject: Subject
    exam: Exam
    deployment: ExamDeployment
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        """
        테스트 전체에서 공유되는 불변 데이터
        """
        # 학생 유저 생성
        cls.student = User.objects.create_user(
            email="student@test.com",
            password="testpass123",
            name="테스트학생",
            birthday=timezone.now().date() - timedelta(days=365 * 20),
            phone_number="010-1234-5678",
            gender="M",
            role=RoleChoices.ST,
        )

        # 강사 유저 생성
        cls.instructor = User.objects.create_user(
            email="instructor@test.com",
            password="testpass123",
            name="테스트강사",
            birthday=timezone.now().date() - timedelta(days=365 * 30),
            phone_number="010-0000-5432",
            gender="F",
            role=RoleChoices.TA,
        )

        cls.course = Course.objects.create(
            name="테스트 코스",
            tag="TC",
            description="테스트용 코스",
        )

        cls.cohort = Cohort.objects.create(
            course=cls.course,
            number=1,
            max_student=30,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=180),
        )

        cls.subject = Subject.objects.create(
            course=cls.course,
            title="테스트 과목",
            number_of_days=5,
            number_of_hours=40,
        )

        cls.exam = Exam.objects.create(
            subject=cls.subject,
            title="테스트 쪽지시험",
        )

        now = timezone.now()
        cls.deployment = ExamDeployment.objects.create(
            cohort=cls.cohort,
            exam=cls.exam,
            duration_time=60,
            access_code="TEST12",
            open_at=now - timedelta(hours=1),
            close_at=now + timedelta(hours=1),
            questions_snapshot=[
                {
                    "id": 1,
                    "type": "single_choice",
                    "question": "테스트 질문 1",
                    "point": 10,
                    "answer": "A",
                    "options": ["A", "B", "C", "D"],
                },
                {
                    "id": 2,
                    "type": "multiple_choice",
                    "question": "테스트 질문 2",
                    "point": 20,
                    "answer": ["A", "B"],
                    "options": ["A", "B", "C", "D"],
                },
                {
                    "id": 3,
                    "type": "fill_blank",
                    "question": "테스트 질문 3",
                    "point": 15,
                    "answer": ["답1", "답2"],
                    "blank_count": 2,
                },
                {
                    "id": 4,
                    "type": "short_answer",
                    "question": "테스트 질문 4",
                    "point": 10,
                    "answer": "정답",
                },
            ],
        )

        cls.url = reverse(
            "exam_cheating_check",
            kwargs={"deployment_id": cls.deployment.pk},
        )

    def setUp(self) -> None:
        """
        테스트마다 새로 생성되는 가변 데이터
        """
        self.client: APIClient = APIClient()

        self.submission = ExamSubmission.objects.create(
            submitter=self.student,
            deployment=self.deployment,
            started_at=timezone.now(),
            cheating_count=0,
            answers={"1": "A"},
            score=0,
            correct_answer_count=0,
        )

        self.url = reverse("exam_cheating_check", kwargs={"deployment_id": self.deployment.pk})

    def test_cheating_event_success_first_time(self) -> None:
        """
        부정행위 1회 적발 성공 테스트
        """
        self.client.force_authenticate(user=self.student)

        response = self.client.post(self.url, data={"event": "focus_out"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["cheating_count"], 1)
        self.assertEqual(response.data["is_forced_submitted"], False)

        # DB 확인
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.cheating_count, 1)

    def test_cheating_event_success_second_time(self) -> None:
        """
        부정행위 2회 적발 성공 테스트
        """
        # 이미 1회 적발된 상태
        self.submission.cheating_count = 1
        self.submission.save()

        self.client.force_authenticate(user=self.student)

        response = self.client.post(self.url, data={"event": "focus_out"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["cheating_count"], 2)
        self.assertEqual(response.data["is_forced_submitted"], False)

        # DB 확인
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.cheating_count, 2)

    def test_cheating_event_success_third_time_force_submit(self) -> None:
        """
        부정행위 3회 적발 시 강제 제출 테스트
        - 현재까지 푼 답까지만 자동 제출, 나머지 문항은 빈 답안으로 자동 채점
        """
        # 이미 2회 적발된 상태로 설정
        self.submission.cheating_count = 2
        self.submission.save()

        self.client.force_authenticate(user=self.student)

        response = self.client.post(self.url, data={"event": "focus_out"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["cheating_count"], 3)
        self.assertEqual(response.data["is_forced_submitted"], True)

        # DB 확인 - 강제 제출로 빈 답안 채워짐
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.cheating_count, 3)

        # 기존 답안 유지 확인
        self.assertEqual(self.submission.answers["1"], "A")

        # 빈 답안 채워진 것 확인
        self.assertIn("2", self.submission.answers)  # 2번 문제 빈 답안
        self.assertIn("3", self.submission.answers)  # 3번 문제 빈 답안
        self.assertIn("4", self.submission.answers)  # 4번 문제 빈 답안

        # 문제 유형별 빈 답안 포맷 확인
        self.assertEqual(self.submission.answers["2"], [])  # multiple_choice
        self.assertEqual(self.submission.answers["3"], ["", ""])  # fill_blank (blank_count=2)
        self.assertEqual(self.submission.answers["4"], "")  # short_answer

        # 자동 채점 확인 (1번 문제만 정답이므로 10점, 1개 정답)
        self.assertEqual(self.submission.score, 10)
        self.assertEqual(self.submission.correct_answer_count, 1)

    def test_cheating_event_invalid_event_type(self) -> None:
        """
        유효하지 않은 이벤트 타입 테스트 (400)
        """
        self.client.force_authenticate(user=self.student)

        response = self.client.post(self.url, data={"event": "invalid_event"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cheating_event_missing_event_field(self) -> None:
        """
        event 필드 누락 테스트 (400)
        """
        self.client.force_authenticate(user=self.student)

        response = self.client.post(self.url, data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cheating_event_deployment_not_found(self) -> None:
        """
        존재하지 않는 deployment 테스트 (404)
        """
        self.client.force_authenticate(user=self.student)

        invalid_url = reverse("exam_cheating_check", kwargs={"deployment_id": 99999})

        response = self.client.post(invalid_url, data={"event": "focus_out"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, EMS.E404_NOT_FOUND("쪽지시험"))

    def test_cheating_event_exam_closed(self) -> None:
        """
        시험 종료 후 요청 테스트 (410 Gone)
        """
        # 시험 종료 상태로 변경
        now = timezone.now()
        self.deployment.close_at = now - timedelta(hours=1)
        self.deployment.save()

        self.client.force_authenticate(user=self.student)

        response = self.client.post(self.url, data={"event": "focus_out"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data, EMS.E410_ALREADY_ENDED("쪽지시험"))

    def test_cheating_event_submission_not_found(self) -> None:
        """
        응시 세션이 존재하지 않는 경우 테스트 (400)
        """
        # 다른 학생 생성 (응시 내역 없음)
        other_student = User.objects.create_user(
            email="other@test.com",
            password="testpass123",
            name="다른학생",
            birthday=timezone.now().date() - timedelta(days=365 * 22),
            phone_number="010-5555-5555",
            gender="F",
            role=RoleChoices.ST,
        )

        self.client.force_authenticate(user=other_student)

        response = self.client.post(self.url, data={"event": "focus_out"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, EMS.E400_INVALID_SESSION("시험 응시"))

    def test_cheating_event_unauthorized(self) -> None:
        """
        인증되지 않은 사용자 테스트 (401)
        """
        response = self.client.post(self.url, data={"event": "focus_out"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cheating_event_forbidden_non_student(self) -> None:
        """
        학생이 아닌 사용자 권한 테스트 (403)
        """
        self.client.force_authenticate(user=self.instructor)

        response = self.client.post(self.url, data={"event": "focus_out"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cheating_event_multiple_increments(self) -> None:
        """
        연속으로 부정행위 발생 시 카운트 증가 테스트
        """
        self.client.force_authenticate(user=self.student)

        # 첫 번째 부정행위
        response1 = self.client.post(self.url, data={"event": "focus_out"}, format="json")
        self.assertEqual(response1.data["cheating_count"], 1)

        # 두 번째 부정행위
        response2 = self.client.post(self.url, data={"event": "focus_out"}, format="json")
        self.assertEqual(response2.data["cheating_count"], 2)

        # 세 번째 부정행위 (강제 제출)
        response3 = self.client.post(self.url, data={"event": "focus_out"}, format="json")
        self.assertEqual(response3.data["cheating_count"], 3)
        self.assertEqual(response3.data["is_forced_submitted"], True)

    def test_force_submit_with_partially_correct_answers(self) -> None:
        """
        일부 정답이 있는 상태에서 강제 제출 시 채점 테스트
        """
        # 1번과 2번 문제만 풀이 (1번 정답, 2번 오답)
        self.submission.answers = {
            "1": "A",  # 정답
            "2": ["A", "C"],  # 오답 (정답: ["A", "B"])
        }
        self.submission.cheating_count = 2
        self.submission.save()

        self.client.force_authenticate(user=self.student)

        response = self.client.post(self.url, data={"event": "focus_out"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 채점 결과 확인
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.score, 10)  # 1번 문제만 정답 (10점)
        self.assertEqual(self.submission.correct_answer_count, 1)

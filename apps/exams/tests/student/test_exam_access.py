from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models import Exam, ExamDeployment
from apps.user.models import User
from apps.user.models.user import GenderChoices, RoleChoices

DEFAULT_DURATION_TIME = 60
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ExamAccessCodeVerifyAPITest(APITestCase):
    """
    쪽지시험 참가 코드 검증 API 테스트
    """

    course: Course
    subject: Subject
    cohort: Cohort
    exam: Exam
    non_student: User
    student: User
    deployment: ExamDeployment
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        # Course / Subject / Exam / Cohort
        cls.course = Course.objects.create(name="테스트 과정")
        cls.subject = Subject.objects.create(
            title="테스트 과목",
            course=cls.course,
            number_of_days=10,
            number_of_hours=20,
        )
        cls.cohort = Cohort.objects.create(
            number=1,
            course=cls.course,
            max_student=20,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        cls.exam = Exam.objects.create(title="테스트 시험", subject=cls.subject)

        # Users
        cls.non_student = User.objects.create_user(
            name="admin",
            password="password123",
            email="admin@test.com",
            phone_number="010-1234-1234",
            gender=GenderChoices.MALE,
            birthday=date.today() + timedelta(days=30),
            role=RoleChoices.USER,
        )
        cls.student = User.objects.create_user(
            password="password123",
            email="user@test.com",
            name="user",
            phone_number="010-1234-5678",
            gender=GenderChoices.FEMALE,
            birthday=date.today() - timedelta(days=30),
            role=RoleChoices.ST,
        )

        # 기본: 현재 응시 가능 deployment
        cls.deployment = ExamDeployment.objects.create(
            exam=cls.exam,
            cohort=cls.cohort,
            duration_time=DEFAULT_DURATION_TIME,
            access_code="ABC123",
            open_at=timezone.now() - timedelta(minutes=10),
            close_at=timezone.now() + timedelta(minutes=30),
            questions_snapshot=[],
        )

    def _get_url(self, deployment_id: int) -> str:
        return reverse(
            "exam-check-code",
            kwargs={"deployment_id": deployment_id},
        )

    def test_unauthenticated_401(self) -> None:
        """
        JWT/인증이 없으면 비즈니스 로직 이전에 차단되어야 한다.
        """
        url = self._get_url(self.deployment.id)
        response = self.client.post(url, data={"code": "ABC123"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_not_student_403(self) -> None:
        """
        인증은 되었지만 role이 학생이 아니면 접근 불가
        """
        self.client.force_authenticate(user=self.non_student)

        url = self._get_url(self.deployment.id)
        response = self.client.post(url, data={"code": "ABC123"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deployment_not_found_404(self) -> None:
        """
        deployment_id가 잘못된 경우 명확히 404 반환
        """
        self.client.force_authenticate(user=self.student)

        url = self._get_url(999999)
        response = self.client.post(url, data={"code": "ABC123"})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "배포 정보을(를) 찾을 수 없습니다.")

    def test_not_yet_opened_423(self) -> None:
        """
        open_at 이전에는 권한이 있어도 응시 불가
        """
        self.client.force_authenticate(user=self.student)

        future_deployment = ExamDeployment.objects.create(
            exam=self.exam,
            cohort=self.cohort,
            duration_time=DEFAULT_DURATION_TIME,
            access_code="DDD444",
            open_at=timezone.now() + timedelta(minutes=10),
            close_at=timezone.now() + timedelta(minutes=30),
            questions_snapshot=[],
        )

        url = self._get_url(future_deployment.id)
        response = self.client.post(url, data={"code": "ABC123"})

        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)

    def test_already_closed_423(self) -> None:
        """
        close_at 이후에도 동일하게 423 처리
        """
        self.client.force_authenticate(user=self.student)

        past_deployment = ExamDeployment.objects.create(
            exam=self.exam,
            cohort=self.cohort,
            duration_time=DEFAULT_DURATION_TIME,
            access_code="BBB123",
            open_at=timezone.now() - timedelta(minutes=30),
            close_at=timezone.now() - timedelta(minutes=10),
            questions_snapshot=[],
        )

        url = self._get_url(past_deployment.id)
        response = self.client.post(url, data={"code": "ABC123"})

        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)

    def test_access_code_is_invalid_400(self) -> None:
        """
        입력은 왔지만 비즈니스 규칙 위반 → 400
        """
        self.client.force_authenticate(user=self.student)

        url = self._get_url(self.deployment.id)
        response = self.client.post(url, data={"code": "WRONG"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error_detail"],
            "응시 코드가 일치하지 않습니다.",
        )

    def test_code_field_is_missing_400(self) -> None:
        """
        serializer 단계에서 차단되는지 확인
        """
        self.client.force_authenticate(user=self.student)

        url = self._get_url(self.deployment.id)
        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", response.data["errors"])

    def test_access_code_is_valid_204(self) -> None:
        """
        모든 조건 충족 시 204 반환
        """
        self.client.force_authenticate(user=self.student)

        url = self._get_url(self.deployment.id)
        response = self.client.post(url, data={"code": "ABC123"})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(response.data)

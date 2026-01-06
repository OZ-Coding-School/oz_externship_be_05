from datetime import date, timedelta
from typing import Any, Dict

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models import Exam, ExamDeployment
from apps.exams.models.exam_deployment import DeploymentStatus
from apps.user.models.user import RoleChoices, User


class ExamDeploymentStatusAPITest(APITestCase):
    """학생용 시험 상태 확인 API 테스트"""

    def setUp(self) -> None:
        self.student = User.objects.create_user(
            name="student1",
            email="student1@example.com",
            password="password",
            role=RoleChoices.ST,
            birthday=date(2000, 1, 1),
        )

        self.course = Course.objects.create(name="테스트 과정")
        self.subject = Subject.objects.create(
            title="테스트 과목",
            course=self.course,
            number_of_days=10,
            number_of_hours=20,
        )
        self.cohort = Cohort.objects.create(
            number=1,
            course=self.course,
            max_student=30,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        self.exam = Exam.objects.create(title="테스트 시험", subject=self.subject)

        # 기본 활성화 상태 배포 생성
        self.deployment = ExamDeployment.objects.create(
            exam=self.exam,
            cohort=self.cohort,
            duration_time=30,
            access_code="ABC123",
            open_at=timezone.now() - timedelta(hours=1),
            close_at=timezone.now() + timedelta(hours=1),
            questions_snapshot=[],
            status=DeploymentStatus.ACTIVATED,
        )

        self.url = reverse("exam_checking_status", args=[self.deployment.id])

    def authenticate_student(self) -> None:
        self.client.force_authenticate(user=self.student)

    def test_active_exam_status(self) -> None:
        """활성화된 시험 상태 확인"""
        self.authenticate_student()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 서비스 로직이 상수를 반환하는지 검증
        self.assertEqual(response.data["exam_status"], DeploymentStatus.ACTIVATED)
        self.assertFalse(response.data["force_submit"])

    def test_expired_exam_status(self) -> None:
        """시험 시간 종료 시 상태 변경 확인"""
        self.deployment.close_at = timezone.now() - timedelta(minutes=5)
        self.deployment.save(update_fields=["close_at"])

        self.authenticate_student()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["exam_status"], DeploymentStatus.DEACTIVATED)
        self.assertTrue(response.data["force_submit"])

    def test_nonexistent_exam_returns_404(self) -> None:
        """존재하지 않는 시험 배포 ID 요청"""
        self.authenticate_student()
        invalid_url = reverse("exam_checking_status", args=[9999])
        response = self.client.get(invalid_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_not_yet_opened_status(self) -> None:
        """시험 오픈 시간 전 상태 확인"""
        self.deployment.open_at = timezone.now() + timedelta(hours=1)
        self.deployment.save(update_fields=["open_at"])

        self.authenticate_student()
        response = self.client.get(self.url)

        # 시작 전인 경우도 진입 불가(DEACTIVATED)로 처리하는지 확인
        self.assertEqual(response.data["exam_status"], DeploymentStatus.DEACTIVATED)
        self.assertTrue(response.data["force_submit"])

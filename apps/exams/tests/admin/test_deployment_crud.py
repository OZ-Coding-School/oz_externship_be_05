from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models import Exam, ExamDeployment
from apps.exams.models.exam_deployment import DeploymentStatus

User = get_user_model()


class DeploymentListAPIViewTests(TestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()

        # 관리자 유저
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="password",
            name="admin",
            birthday=date(2000, 12, 12),
            is_staff=True,
            is_superuser=True,
        )

        # 일반 유저
        self.user = User.objects.create_user(
            email="user@test.com",
            password="password",
            name="user",
            birthday=date(1990, 11, 1),
        )

        # 기본 데이터
        self.course = Course.objects.create(name="테스트 과정")

        self.subject = Subject.objects.create(
            course=self.course,
            title="테스트 과목",
            number_of_days=1,
            number_of_hours=1,
        )

        self.cohort = Cohort.objects.create(
            course=self.course,
            number=1,
            max_student=20,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )

        self.exam = Exam.objects.create(
            subject=self.subject,
            title="테스트 시험",
        )

        self.url = reverse("deployment")

    def _create_deployment(self) -> None:
        """
        기본 데이터 생성 헬퍼 함수
        """
        ExamDeployment.objects.create(
            exam=self.exam,
            cohort=self.cohort,
            duration_time=30,
            open_at=timezone.now() + timedelta(days=1),
            close_at=timezone.now() + timedelta(days=2),
            status=DeploymentStatus.DEACTIVATED,
            access_code="testcode",
            questions_snapshot={},
        )

    def test_list_deployments_success(self) -> None:
        """
        200 OK
        """
        self._create_deployment()

        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["total_count"], 1)
        self.assertEqual(len(response.data["deployments"]), 1)

    def test_invalid_page_param(self) -> None:
        """
        400 - page/size 타입 오류
        """
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"page": "abc"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error_detail"],
            "유효하지 않은 요청입니다.",
        )

    def test_invalid_cohort_id(self) -> None:
        """
        400 - 잘못된 cohort_id
        """
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"cohort_id": 9999})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error_detail"],
            "유효하지 않은 요청입니다.",
        )

    def test_no_deployment_exists(self) -> None:
        """
        404 - 데이터 없음
        """
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["error_detail"],
            "등록된 배포 내역이 없습니다.",
        )

    def test_page_out_of_range(self) -> None:
        """
        404 - page 범위 초과
        """

        self._create_deployment()

        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"page": 10})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["error_detail"],
            "등록된 배포 내역이 없습니다.",
        )

    def test_permission_denied_for_non_admin(self) -> None:
        """
        403 - 관리자 아님
        """
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

from datetime import timedelta
from typing import Any

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models import Exam, ExamDeployment, ExamQuestion
from apps.exams.models.exam_deployment import DeploymentStatus
from apps.exams.models.exam_question import QuestionType
from apps.exams.services.admin.admin_deployment_service import (
    create_deployment,
    delete_deployment,
    get_admin_deployment_detail,
    list_admin_deployments,
    set_deployment_status,
    update_deployment,
)


class DeploymentServiceTests(TestCase):
    course: Course
    subject: Subject
    exam: Exam

    # SETUP ---------------------------------------------------------
    @classmethod
    def setUpTestData(cls) -> None:
        cls.course = Course.objects.create(name="완소 퍼펙트 공주")

        cls.subject = Subject.objects.create(
            course=cls.course,
            title="공주를 위한 예절 a to z",
            number_of_days=30,
            number_of_hours=60,
        )

        cls.exam = Exam.objects.create(
            title="공주예절 시험",
            subject=cls.subject,
        )

        ExamQuestion.objects.create(
            exam=cls.exam,
            question="Q1",
            prompt="",
            blank_count=0,
            options=[],
            type=QuestionType.SHORT_ANSWER,
            answer="A",
            point=10,
            explanation="",
        )
        ExamQuestion.objects.create(
            exam=cls.exam,
            question="Q2",
            prompt="",
            blank_count=0,
            options=[],
            type=QuestionType.SHORT_ANSWER,
            answer="B",
            point=10,
            explanation="",
        )

    def setUp(self) -> None:
        self.cohort = Cohort.objects.create(
            course=self.course,
            number=1,
            max_student=30,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
        )

        self.open_at = timezone.now() + timedelta(hours=1)
        self.close_at = self.open_at + timedelta(hours=1)

    # Helpers ---------------------------------------------------------

    def _create_default_deployment(self, **override: Any) -> ExamDeployment:

        base: dict[str, Any] = {
            "cohort": self.cohort,
            "exam": self.exam,
            "duration_time": 60,
            "open_at": self.open_at,
            "close_at": self.close_at,
        }

        params = {**base, **override}

        return create_deployment(**params)

    def _force_started(self, deployment: ExamDeployment) -> ExamDeployment:
        deployment.open_at = timezone.now() - timedelta(hours=1)
        deployment.save(update_fields=["open_at"])
        return deployment

    def _force_closed(self, deployment: ExamDeployment) -> ExamDeployment:
        deployment.close_at = timezone.now() - timedelta(minutes=1)
        deployment.save(update_fields=["close_at"])
        return deployment

    # CREATE ---------------------------------------------------------

    def test_create_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        self.assertIsNotNone(deployment.id)
        self.assertEqual(deployment.status, DeploymentStatus.ACTIVATED)
        self.assertEqual(len(deployment.questions_snapshot), 2)

    def test_create_deployment_with_past_open_at(self) -> None:
        deployment = self._create_default_deployment(open_at=timezone.now() - timedelta(hours=1))
        self.assertIsNotNone(deployment.id)

    def test_create_deployment_with_invalid_time_range(self) -> None:
        deployment = self._create_default_deployment(
            open_at=self.close_at,
            close_at=self.close_at,
        )
        self.assertIsNotNone(deployment.id)

    # UPDATE ---------------------------------------------------------

    def test_update_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        updated = update_deployment(
            deployment=deployment,
            data={"duration_time": 90},
        )
        self.assertEqual(updated.duration_time, 90)

    def test_update_started_deployment_allows_update(self) -> None:
        deployment = self._create_default_deployment()
        self._force_started(deployment)

        with self.assertRaises(ValidationError):
            update_deployment(
                deployment=deployment,
                data={"open_at": timezone.now() + timedelta(hours=10)},
            )

    # STATUS ---------------------------------------------------------

    def test_set_status_success(self) -> None:
        deployment = self._create_default_deployment()
        updated = set_deployment_status(
            deployment=deployment,
            status=DeploymentStatus.DEACTIVATED,
        )
        self.assertEqual(updated.status, DeploymentStatus.DEACTIVATED)

    def test_set_status_after_closed(self) -> None:
        deployment = self._create_default_deployment()
        self._force_closed(deployment)

        updated = set_deployment_status(
            deployment=deployment,
            status=DeploymentStatus.DEACTIVATED,
        )

        self.assertEqual(updated.status, DeploymentStatus.DEACTIVATED)

    # DELETE ---------------------------------------------------------

    def test_delete_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        delete_deployment(deployment=deployment)

        with self.assertRaises(ExamDeployment.DoesNotExist):
            ExamDeployment.objects.get(id=deployment.id)

    def test_delete_started_deployment(self) -> None:
        deployment = self._create_default_deployment()
        self._force_started(deployment)

        with self.assertRaises(ValidationError):
            delete_deployment(deployment=deployment)

    # LIST ---------------------------------------------------------

    def test_list_deployments_default(self) -> None:
        d1 = self._create_default_deployment()
        d2 = self._create_default_deployment(
            open_at=self.open_at + timedelta(hours=1),
            close_at=self.close_at + timedelta(hours=1),
        )

        deployments = list_admin_deployments()
        self.assertEqual(deployments.count(), 2)

        first = deployments.first()
        last = deployments.last()

        assert first is not None
        assert last is not None

        self.assertEqual(first.id, d2.id)
        self.assertEqual(last.id, d1.id)

    def test_list_deployments_filter_by_cohort(self) -> None:
        other_cohort = Cohort.objects.create(
            course=self.exam.subject.course,
            number=99,
            max_student=30,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
        )

        d1 = self._create_default_deployment()
        self._create_default_deployment(cohort=other_cohort)

        deployments = list_admin_deployments(cohort=self.cohort)
        self.assertEqual(deployments.count(), 1)

        first = deployments.first()
        assert first is not None

        self.assertEqual(first.id, d1.id)

    def test_list_deployments_filter_by_status(self) -> None:
        d1 = self._create_default_deployment()
        self._create_default_deployment()

        set_deployment_status(
            deployment=d1,
            status=DeploymentStatus.DEACTIVATED,
        )

        deployments = list_admin_deployments(status=DeploymentStatus.DEACTIVATED)
        self.assertEqual(deployments.count(), 1)

        first = deployments.first()
        assert first is not None

        self.assertEqual(first.id, d1.id)

    # GET ---------------------------------------------------------

    def test_get_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        found = get_admin_deployment_detail(deployment_id=deployment.id)

        self.assertEqual(found.id, deployment.id)
        self.assertEqual(found.exam.id, self.exam.id)

    def test_get_deployment_fail(self) -> None:
        with self.assertRaises(Exception):
            get_admin_deployment_detail(deployment_id=999)

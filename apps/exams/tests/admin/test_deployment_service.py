from datetime import datetime, timedelta
from typing import Any

from django.db.models import QuerySet
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
    get_deployment,
    list_deployments,
    set_deployment_status,
    update_deployment,
)


class DeploymentServiceTests(TestCase):

    def setUp(self) -> None:
        self.course = Course.objects.create(name="완소 퍼펙트 공주")
        self.subject = Subject.objects.create(
            name="공주를 위한 예절 a to z",  # type: ignore[misc]
            course=self.course,
        )
        self.exam = Exam.objects.create(
            title="공주예절 시험",
            subject=self.subject,
        )

        ExamQuestion.objects.create(
            exam=self.exam,
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
            exam=self.exam,
            question="Q2",
            prompt="",
            blank_count=0,
            options=[],
            type=QuestionType.SHORT_ANSWER,
            answer="B",
            point=10,
            explanation="",
        )

        self.cohort = Cohort.objects.create(
            name="1기",  # type: ignore[misc]
            course=self.course,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
        )

        self.open_at, self.close_at = self._future_times()

    # Helpers ---------------------------------------------------------

    @staticmethod
    def _future_times() -> tuple[datetime, datetime]:
        open_at = timezone.now() + timedelta(hours=1)
        close_at = open_at + timedelta(hours=1)
        return open_at, close_at

    @staticmethod
    def _past_times() -> tuple[datetime, datetime]:
        open_at = timezone.now() - timedelta(hours=2)
        close_at = timezone.now() - timedelta(hours=1)
        return open_at, close_at

    def _create_default_deployment(self, **override: Any) -> ExamDeployment:
        params = dict(
            cohort=self.cohort,
            exam=self.exam,
            duration_time=60,
            access_code="000",
            open_at=self.open_at,
            close_at=self.close_at,
        )
        params.update(override)
        return create_deployment(**params)  # type: ignore[arg-type]

    # CREATE ---------------------------------------------------------

    def test_create_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        self.assertIsNotNone(deployment.id)
        self.assertEqual(deployment.status, DeploymentStatus.ACTIVATED)
        self.assertEqual(len(deployment.questions_snapshot), 2)

    def test_create_deployment_fail_open_at_past(self) -> None:
        with self.assertRaises(ValidationError):
            self._create_default_deployment(open_at=timezone.now() - timedelta(hours=1))

    def test_create_deployment_fail_course_mismatch(self) -> None:
        other_course = Course.objects.create(name="공주의 스타일기")
        other_cohort = Cohort.objects.create(
            name="2기",  # type: ignore[misc]
            course=other_course,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
        )

        with self.assertRaises(ValidationError):
            self._create_default_deployment(cohort=other_cohort)

    def test_create_deployment_fail_open_after_close(self) -> None:
        with self.assertRaises(ValidationError):
            self._create_default_deployment(open_at=self.close_at, close_at=self.close_at)

    # UPDATE ---------------------------------------------------------

    def test_update_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        updated = update_deployment(deployment=deployment, data={"duration_time": 90})
        self.assertEqual(updated.duration_time, 90)

    def test_update_deployment_fail_started_open_at_change(self) -> None:
        past_open, past_close = self._past_times()
        deployment = self._create_default_deployment(open_at=past_open, close_at=past_close)

        with self.assertRaises(ValidationError):
            update_deployment(
                deployment=deployment,
                data={"open_at": timezone.now() + timedelta(hours=10)},
            )

    # STATUS ---------------------------------------------------------

    def test_set_status_success(self) -> None:
        deployment = self._create_default_deployment()
        updated = set_deployment_status(deployment=deployment, status=DeploymentStatus.DEACTIVATED)
        self.assertEqual(updated.status, DeploymentStatus.DEACTIVATED)

    def test_set_status_fail_after_closed(self) -> None:
        closed_open, closed_close = self._past_times()
        deployment = self._create_default_deployment(open_at=closed_open, close_at=closed_close)

        with self.assertRaises(ValidationError):
            set_deployment_status(deployment=deployment, status=DeploymentStatus.DEACTIVATED)

    # DELETE ---------------------------------------------------------

    def test_delete_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        delete_deployment(deployment=deployment)

        with self.assertRaises(ExamDeployment.DoesNotExist):
            ExamDeployment.objects.get(id=deployment.id)

    def test_delete_deployment_fail_already_started(self) -> None:
        past_open = timezone.now() - timedelta(hours=1)
        past_close = timezone.now() + timedelta(hours=1)

        deployment = self._create_default_deployment(open_at=past_open, close_at=past_close)

        with self.assertRaises(ValidationError):
            delete_deployment(deployment=deployment)

    # LIST ---------------------------------------------------------

    def test_list_deployments_default(self) -> None:
        d1 = self._create_default_deployment(access_code="111")
        d2 = self._create_default_deployment(
            access_code="222",
            open_at=self.open_at + timedelta(hours=1),
            close_at=self.close_at + timedelta(hours=1),
        )

        deployments = list_deployments()
        self.assertEqual(deployments.count(), 2)
        self.assertEqual(deployments.first().id, d2.id)  # type: ignore[union-attr]
        self.assertEqual(deployments.last().id, d1.id)  # type: ignore[union-attr]

    def test_list_deployments_filter_by_cohort(self) -> None:
        other_course = Course.objects.create(name="공주를 위한 댄스 기초")
        other_cohort = Cohort.objects.create(
            name="99기",  # type: ignore[misc]
            course=other_course,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
        )

        d1 = self._create_default_deployment()
        self._create_default_deployment(cohort=other_cohort)

        deployments = list_deployments(cohort=self.cohort)
        self.assertEqual(deployments.count(), 1)
        self.assertEqual(deployments.first().id, d1.id)  # type: ignore[union-attr]

    def test_list_deployments_filter_by_status(self) -> None:
        d1 = self._create_default_deployment(access_code="111")
        self._create_default_deployment(access_code="222")

        set_deployment_status(deployment=d1, status=DeploymentStatus.DEACTIVATED)

        deployments = list_deployments(status=DeploymentStatus.DEACTIVATED)
        self.assertEqual(deployments.count(), 1)
        self.assertEqual(deployments.first().id, d1.id)  # type: ignore[union-attr]

    # GET ---------------------------------------------------------

    def test_get_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        found = get_deployment(deployment_id=deployment.id)
        self.assertEqual(found.id, deployment.id)
        self.assertEqual(found.exam.id, self.exam.id)

    def test_get_deployment_fail(self) -> None:
        with self.assertRaises(ValidationError):
            get_deployment(deployment_id=999)

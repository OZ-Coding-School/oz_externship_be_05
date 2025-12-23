from datetime import timedelta
from typing import Any

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.courses.models import Cohort, Course, Subject
from apps.exams.exceptions import DeploymentConflictException
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
        self._deployment_counter = getattr(self, "_deployment_counter", 0) + 1
        offset = timedelta(minutes=10 * self._deployment_counter)

        pop = override.pop

        cohort = pop("cohort", None) or Cohort.objects.create(
            course=self.course,
            number=100 + self._deployment_counter,  # 중복 방지
            max_student=30,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
        )

        exam = pop("exam", self.exam)
        open_at = pop("open_at", self.open_at + offset)
        close_at = pop("close_at", self.close_at + offset)

        deployment = create_deployment(
            cohort=cohort,
            exam=exam,
            duration_time=60,
            open_at=open_at,
            close_at=close_at,
        )

        return deployment

    def _force_started(self, deployment: ExamDeployment) -> ExamDeployment:
        deployment.open_at = timezone.now() - timedelta(hours=1)
        deployment.save(update_fields=["open_at"])
        return deployment

    def _force_closed(self, deployment: ExamDeployment) -> ExamDeployment:
        deployment.close_at = timezone.now() - timedelta(minutes=1)
        deployment.save(update_fields=["close_at"])
        return deployment

    def _force_finished(self, deployment: ExamDeployment) -> ExamDeployment:
        deployment.open_at = timezone.now() - timedelta(hours=2)
        deployment.close_at = timezone.now() - timedelta(hours=1)
        deployment.status = DeploymentStatus.DEACTIVATED
        deployment.save(update_fields=["open_at", "close_at", "status"])
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
        self._create_default_deployment(
            open_at=self.close_at,
            close_at=self.close_at,
        )

        deployment = ExamDeployment.objects.get()

        self.assertGreaterEqual(deployment.open_at, deployment.close_at)

    # 중복 배포 예외처리
    def test_create_duplicate_deployment(self) -> None:
        deployment = self._create_default_deployment()

        # 중복 배포 시도
        with self.assertRaises(DeploymentConflictException) as cm:
            self._create_default_deployment(cohort=deployment.cohort, exam=deployment.exam)

        self.assertIn(
            f"동일한 조건의 배포가 이미 존재합니다: '{deployment.exam.title}' - {deployment.cohort.number}기",
            str(cm.exception),
        )

    # 이미 활성화된 시험 예외처리
    def test_create_deployment_with_active_conflict(self) -> None:
        deployment = self._create_default_deployment()

        deployment.status = DeploymentStatus.ACTIVATED
        deployment.open_at = timezone.now() - timedelta(hours=1)
        deployment.save(update_fields=["status", "open_at"])

        with self.assertRaises(DeploymentConflictException) as cm:
            self._create_default_deployment(cohort=deployment.cohort, exam=deployment.exam)

        self.assertIn(
            f"동일한 조건의 배포가 이미 존재합니다: '{deployment.exam.title}' - {deployment.cohort.number}기",
            str(cm.exception),
        )

    # UPDATE ---------------------------------------------------------

    def test_update_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        updated = update_deployment(
            deployment=deployment,
            data={"duration_time": 90},
        )
        self.assertEqual(updated.duration_time, 90)

    def test_update_started_deployment_raises_error(self) -> None:
        deployment = self._create_default_deployment()
        self._force_started(deployment)

        with self.assertRaises(ValidationError) as ve:
            update_deployment(
                deployment=deployment,
                data={"open_at": timezone.now() + timedelta(hours=10)},
            )

        self.assertIn("open_at", ve.exception.detail)

    def test_update_finished_deployment_raises_error(self) -> None:
        deployment = self._create_default_deployment()
        self._force_finished(deployment)

        with self.assertRaises(ValidationError) as ve:
            update_deployment(
                deployment=deployment,
                data={"duration_time": 90},
            )

        self.assertIn("status", ve.exception.detail)

    # STATUS ---------------------------------------------------------

    def test_set_status_success(self) -> None:
        deployment = self._create_default_deployment()
        updated = set_deployment_status(
            deployment=deployment,
            status=DeploymentStatus.DEACTIVATED,
        )
        self.assertEqual(updated.status, DeploymentStatus.DEACTIVATED)

    def test_set_status_after_closed_raises_error(self) -> None:
        deployment = self._create_default_deployment()
        self._force_finished(deployment)

        with self.assertRaises(ValidationError) as ve:
            set_deployment_status(
                deployment=deployment,
                status=DeploymentStatus.ACTIVATED,
            )

        self.assertIn("status", ve.exception.detail)

    def test_set_status_early_termination_allows_reactivation(self) -> None:
        deployment = self._create_default_deployment()

        # 조기 종료(close_at 전에 DEACTIVATED)
        set_deployment_status(
            deployment=deployment,
            status=DeploymentStatus.DEACTIVATED,
        )

        # 재활성화
        updated = set_deployment_status(
            deployment=deployment,
            status=DeploymentStatus.ACTIVATED,
        )

        self.assertEqual(updated.status, DeploymentStatus.ACTIVATED)

    # DELETE ---------------------------------------------------------

    def test_delete_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        delete_deployment(deployment=deployment)

        with self.assertRaises(ExamDeployment.DoesNotExist):
            ExamDeployment.objects.get(id=deployment.id)

    # 시작된 시험도 가능
    def test_delete_started_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        self._force_started(deployment)

        delete_deployment(deployment=deployment)

        with self.assertRaises(ExamDeployment.DoesNotExist):
            ExamDeployment.objects.get(id=deployment.id)

    # 종료된 시험도 가능
    def test_delete_finished_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        self._force_finished(deployment)

        delete_deployment(deployment=deployment)

        with self.assertRaises(ExamDeployment.DoesNotExist):
            ExamDeployment.objects.get(id=deployment.id)

    # LIST ---------------------------------------------------------

    # 기본 정렬
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

    # 기수별 필터링
    def test_list_deployments_filter_by_cohort(self) -> None:
        other_cohort = Cohort.objects.create(
            course=self.exam.subject.course,
            number=99,
            max_student=30,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
        )

        # self.cohort 배포 명시 생성
        d1 = self._create_default_deployment(cohort=self.cohort)
        # 다른 cohort 배포
        self._create_default_deployment(cohort=other_cohort)

        deployments = list_admin_deployments(cohort=self.cohort)
        self.assertEqual(deployments.count(), 1)

        first = deployments.first()
        assert first is not None

        self.assertEqual(first.id, d1.id)

    # 시험 제목 키워드 검색
    def test_list_deployments_search_by_keyword(self) -> None:
        other_exam = Exam.objects.create(
            title="왕자예절 시험",
            subject=self.subject,
        )

        d1 = self._create_default_deployment()  # 공주예절 시험
        self._create_default_deployment(exam=other_exam)  # 왕자예절 시험

        # 공주로 검색
        deployments = list_admin_deployments(search_keyword="공주")
        self.assertEqual(deployments.count(), 1)

        first = deployments.first()
        assert first is not None
        self.assertEqual(first.id, d1.id)

    # 응시자 수 기준 정렬 (많은 순)
    def test_list_deployments_sort_by_participant_count(self) -> None:
        d1 = self._create_default_deployment()
        d2 = self._create_default_deployment(
            open_at=self.open_at + timedelta(hours=1),
            close_at=self.close_at + timedelta(hours=1),
        )

        deployments = list_admin_deployments(sort="participant_count", order="desc")
        self.assertEqual(deployments.count(), 2)

    # 평균 점수 기준 정렬 (높은 순)
    def test_list_deployments_sort_by_avg_score(self) -> None:
        d1 = self._create_default_deployment()
        d2 = self._create_default_deployment(
            open_at=self.open_at + timedelta(hours=1),
            close_at=self.close_at + timedelta(hours=1),
        )

        deployments = list_admin_deployments(sort="avg_score", order="desc")
        self.assertEqual(deployments.count(), 2)

    # 잘못된 기준을 주면 created_at으로 제공
    def test_list_deployments_invalid_sort_defaults_to_created_at(self) -> None:
        d1 = self._create_default_deployment()
        d2 = self._create_default_deployment(
            open_at=self.open_at + timedelta(hours=1),
            close_at=self.close_at + timedelta(hours=1),
        )

        # 잘못된 sort 값
        deployments = list_admin_deployments(sort="invalid_field", order="desc")
        self.assertEqual(deployments.count(), 2)

        # created_at 기준 내림차순이므로 d2가 먼저
        first = deployments.first()
        assert first is not None
        self.assertEqual(first.id, d2.id)

    # GET ---------------------------------------------------------

    def test_get_deployment_success(self) -> None:
        deployment = self._create_default_deployment()
        found = get_admin_deployment_detail(deployment_id=deployment.id)

        self.assertEqual(found.id, deployment.id)
        self.assertEqual(found.exam_id, self.exam.id)

    def test_get_deployment_fail(self) -> None:
        with self.assertRaises(ValidationError):
            get_admin_deployment_detail(deployment_id=999)

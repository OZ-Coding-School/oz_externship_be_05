from datetime import datetime, timedelta
from typing import Any, Dict

from django.test import TestCase
from django.utils import timezone

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models import Exam, ExamDeployment
from apps.exams.serializers.admin.admin_deployment_serializer import (
    ExamDeploymentPatchSerializer,
    ExamDeploymentPostSerializer,
)


class AdminDeploymentSerializerTest(TestCase):
    course: Course
    subject: Subject
    exam: Exam
    cohort: Cohort

    @classmethod
    def setUpTestData(cls) -> None:
        # course
        cls.course = Course.objects.create(
            name="공주의 규칙",
            tag="PR",
            description="완소 퍼펙트 프린세스를 위한 과정",
        )

        # subject
        cls.subject = Subject.objects.create(
            title="공주를 위한 예절 a to z",
            course=cls.course,
            number_of_days=1,
            number_of_hours=1,
        )

        # exam
        cls.exam = Exam.objects.create(
            subject=cls.subject,
            title="공주예절 시험",
        )

        # cohort
        cls.cohort = Cohort.objects.create(
            course=cls.course,
            number=1,
            max_student=20,
            start_date=timezone.make_aware(datetime(2025, 1, 1)),
            end_date=timezone.make_aware(datetime(2025, 2, 1)),
        )

    def test_create_valid(self) -> None:
        # 정상 데이터는 serializer.is_valid() == True
        data: Dict[str, Any] = {
            "cohort_id": self.cohort.id,
            "exam_id": self.exam.id,
            "duration_time": 60,
            "open_at": timezone.now() + timedelta(hours=1),
            "close_at": timezone.now() + timedelta(hours=2),
            "status": "activated",
        }

        serializer = ExamDeploymentPostSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_invalid_open_in_past(self) -> None:
        # 생성 시 open_at 이 과거면 실패

        data: Dict[str, Any] = {
            "cohort_id": self.cohort.id,
            "exam_id": self.exam.id,
            "duration_time": 60,
            "open_at": timezone.now() - timedelta(hours=1),  # 과거 = 오류
            "close_at": timezone.now() + timedelta(hours=1),
            "status": "activated",
        }

        serializer = ExamDeploymentPostSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("open_at", serializer.errors)

    def test_update_allow_past_open_at(self) -> None:
        # 수정 시 open_at 이 과거여도 허용
        deployment = ExamDeployment.objects.create(
            cohort=self.cohort,
            exam=self.exam,
            duration_time=60,
            access_code="공주변경",
            open_at=timezone.make_aware(datetime(2025, 1, 1, 10, 0)),
            close_at=timezone.make_aware(datetime(2025, 2, 1, 11, 0)),
            status="activated",
            questions_snapshot={},
        )

        serializer = ExamDeploymentPatchSerializer(
            instance=deployment,
            data={},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_invalid_time(self) -> None:
        # open_at >= close_at 일 경우 ValidationError

        data: Dict[str, Any] = {
            "cohort_id": self.cohort.id,
            "exam_id": self.exam.id,
            "duration_time": 60,
            "open_at": timezone.now() + timedelta(hours=2),
            "close_at": timezone.now() + timedelta(hours=1),
            "status": "activated",
        }

        serializer = ExamDeploymentPostSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("open_at", serializer.errors)

    def test_invalid_exam_cohort_course_mismatch(self) -> None:
        # exam의 course - cohort의 course가 다르면 오류
        other_course = Course.objects.create(
            name="공주의 생존규칙",
            tag="PS",
            description="공주를 위한 생존 교육",
        )

        other_cohort = Cohort.objects.create(
            course=other_course,
            number=1,
            max_student=20,
            start_date=timezone.make_aware(datetime(2025, 1, 1)),
            end_date=timezone.make_aware(datetime(2025, 2, 1)),
        )

        data: Dict[str, Any] = {
            "cohort_id": other_cohort.id,
            "exam_id": self.exam.id,  # 다른 코스의 exam
            "duration_time": 60,
            "open_at": timezone.now() + timedelta(hours=1),
            "close_at": timezone.now() + timedelta(hours=2),
            "status": "activated",
        }

        serializer = ExamDeploymentPostSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("cohort_id", serializer.errors)

    def test_update_time_order_validation(self) -> None:
        # 수정 - 시간 검증
        deployment = ExamDeployment.objects.create(
            cohort=self.cohort,
            exam=self.exam,
            duration_time=60,
            access_code="공주수정",
            open_at=timezone.now() + timedelta(hours=1),
            close_at=timezone.now() + timedelta(hours=2),
            status="activated",
            questions_snapshot={},
        )

        # close_at < open_at 시도
        serializer = ExamDeploymentPatchSerializer(
            instance=deployment,
            data={"close_at": timezone.now() - timedelta(hours=1)},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("open_at", serializer.errors)

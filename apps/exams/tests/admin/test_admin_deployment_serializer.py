from datetime import datetime, timedelta
from typing import Any, Dict

from django.test import TestCase
from django.utils import timezone

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models import Exam, ExamDeployment
from apps.exams.serializers.admin.admin_deployment_serializer import (
    AdminDeploymentSerializer,
)


class AdminDeploymentSerializerTest(TestCase):

    def setUp(self) -> None:
        # course
        self.course: Course = Course.objects.create(
            name="공주의 규칙",
            tag="PR",
            description="완소 퍼펙트 프린세스를 위한 과정",
        )

        # subject
        self.subject: Subject = Subject.objects.create(
            title="공주를 위한 예절 a to z",
            course=self.course,
            number_of_days=1,
            number_of_hours=1,
        )

        # exam
        self.exam: Exam = Exam.objects.create(subject=self.subject, title="공주예절 시험")

        # cohort
        self.cohort: Cohort = Cohort.objects.create(
            course=self.course,
            number=1,
            max_student=20,
            start_date=timezone.make_aware(datetime(2025, 1, 1)),
            end_date=timezone.make_aware(datetime(2025, 2, 1)),
        )

    def test_create_valid(self) -> None:
        # 정상 데이터는 serializer.is_valid() == True
        data: Dict[str, Any] = {
            "cohort": self.cohort.id,
            "exam": self.exam.id,
            "duration_time": 60,
            "access_code": "공주등장",
            "open_at": timezone.now() + timedelta(hours=1),
            "close_at": timezone.now() + timedelta(hours=2),
            "status": "activated",
        }

        serializer = AdminDeploymentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_invalid_open_in_past(self) -> None:
        # 생성 시 open_at 이 과거면 실패

        data: Dict[str, Any] = {
            "cohort": self.cohort.id,
            "exam": self.exam.id,
            "duration_time": 60,
            "access_code": "공주실패",
            "open_at": timezone.now() - timedelta(hours=1),  # 과거 = 오류
            "close_at": timezone.now() + timedelta(hours=1),
            "status": "activated",
        }

        serializer = AdminDeploymentSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

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

        data: Dict[str, Any] = {"status": "activated"}

        serializer = AdminDeploymentSerializer(
            instance=deployment,
            data=data,
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

    def test_serializer_invalid_time(self) -> None:
        # open_at >= close_at 일 경우 ValidationError

        data: Dict[str, Any] = {
            "cohort": self.cohort.id,
            "exam": self.exam.id,
            "duration_time": 60,
            "access_code": "WHERE_IS_PRINCE",
            "open_at": timezone.now() + timedelta(hours=2),
            "close_at": timezone.now() + timedelta(hours=1),
            "status": "activated",
        }

        serializer = AdminDeploymentSerializer(data=data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

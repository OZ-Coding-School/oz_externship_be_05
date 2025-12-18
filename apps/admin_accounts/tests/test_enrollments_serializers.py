from typing import ClassVar

from django.test import TestCase

from apps.admin_accounts.serializers.enrollments import (
    AdminAccountStudentEnrollAcceptSerializer,
    AdminAccountStudentEnrollRejectRequestSerializer,
    AdminAccountStudentEnrollRejectResponseSerializer,
    AdminAccountStudentEnrollSerializer,
    AdminAccountStudentSerializer,
)
from apps.admin_accounts.tests.utils.factories import (
    make_cohort,
    make_course,
    make_user,
)
from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course
from apps.user.models import User
from apps.user.models.enrollment import StudentEnrollmentRequest


class EnrollmentSerializersTests(TestCase):
    user: ClassVar[User]
    course: ClassVar[Course]
    cohort: ClassVar[Cohort]
    enrollment: ClassVar[StudentEnrollmentRequest]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = make_user(email="s@test.com", nickname="snick")
        cls.course = make_course(name="Backend", tag="BE")
        cls.cohort = make_cohort(course=cls.course, number=1)

        cls.enrollment = StudentEnrollmentRequest.objects.create(
            user=cls.user,
            cohort=cls.cohort,
            status="PENDING",
        )

    def test_student_serializer_shape(self) -> None:
        data = AdminAccountStudentSerializer(instance=self.user).data
        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "email",
                "nickname",
                "name",
                "phone_number",
                "birthday",
                "status",
                "role",
                "in_progress_course",
                "created_at",
            },
        )

    def test_enroll_serializer_shape(self) -> None:
        data = AdminAccountStudentEnrollSerializer(instance=self.enrollment).data
        self.assertEqual(set(data.keys()), {"id", "user", "cohort", "course", "status", "created_at"})
        self.assertEqual(data["status"], "PENDING")

    def test_accept_serializer_valid(self) -> None:
        s = AdminAccountStudentEnrollAcceptSerializer(data={"detail": "ok", "success": 1, "failed": 0})
        self.assertTrue(s.is_valid(), s.errors)

    def test_reject_request_serializer_invalid_empty(self) -> None:
        s = AdminAccountStudentEnrollRejectRequestSerializer(data={"enrollments": []})
        self.assertFalse(s.is_valid())

    def test_reject_response_serializer_invalid_type(self) -> None:
        s = AdminAccountStudentEnrollRejectResponseSerializer(data={"detail": "no", "success": "abc", "failed": 0})
        self.assertFalse(s.is_valid())
        self.assertIn("success", s.errors)

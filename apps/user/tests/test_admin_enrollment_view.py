from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course
from apps.user.models import (
    CohortStudent,
    EnrollmentStatus,
    StudentEnrollmentRequest,
    User,
)
from apps.user.models.user import RoleChoices
from apps.user.views.admin.enrollments import (
    AdminStudentEnrollAcceptView,
    AdminStudentEnrollRejectView,
    AdminStudentsEnrollViews,
    AdminStudentView,
)


class AdminStudentAPIMinimalTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="pass1234!",
            name="슈퍼유저",
            nickname="admin",
            phone_number="01000000000",
            birthday=date(1998, 1, 4),
            role=RoleChoices.AD,  # ✅ 이거 추가
        )

        self.course1 = Course.objects.create(name="초격차 백엔드 부트캠프", tag="BE")
        self.course2 = Course.objects.create(name="프론트 부트캠프", tag="FE")

        start = date(2025, 1, 1)
        end = start + timedelta(days=180)

        self.cohort1_1 = Cohort.objects.create(
            course=self.course1, number=1, max_student=30, start_date=start, end_date=end
        )
        self.cohort1_2 = Cohort.objects.create(
            course=self.course1, number=2, max_student=30, start_date=start, end_date=end
        )
        self.cohort2_1 = Cohort.objects.create(
            course=self.course2, number=1, max_student=30, start_date=start, end_date=end
        )

        self.st1 = User.objects.create_user(
            email="st1@example.com",
            password="pass1234!",
            name="학생1",
            nickname="st1",
            phone_number="01000000001",
            birthday=date(1998, 8, 29),
            role=RoleChoices.ST,
        )
        self.st2 = User.objects.create_user(
            email="st2@example.com",
            password="pass1234!",
            name="학생2",
            nickname="st2",
            phone_number="01000000002",
            birthday=date(1999, 8, 29),
            role=RoleChoices.ST,
        )

        CohortStudent.objects.create(user=self.st1, cohort=self.cohort1_1)
        CohortStudent.objects.create(user=self.st2, cohort=self.cohort2_1)

    def test_admin_student_list_filters_by_course_and_cohort_number(self) -> None:
        request = self.factory.get(
            "/admin/students",
            {"course_id": self.course1.id, "cohort_number": 1},
        )
        force_authenticate(request, user=self.admin)

        response = AdminStudentView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)

        # course1 1기에는 st1만 있음
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["email"], "st1@example.com")

    def test_admin_student_list_search_by_email(self) -> None:
        request = self.factory.get("/admin/students", {"search": "st2@"})
        force_authenticate(request, user=self.admin)

        response = AdminStudentView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["email"], "st2@example.com")

    def test_admin_enrollment_list_status_filter(self) -> None:
        e1 = StudentEnrollmentRequest.objects.create(
            user=self.st1,
            cohort=self.cohort1_2,
            status=EnrollmentStatus.PENDING,
        )
        e2 = StudentEnrollmentRequest.objects.create(
            user=self.st2,
            cohort=self.cohort2_1,
            status=EnrollmentStatus.ACCEPTED,
        )

        request = self.factory.get("/admin/enrollments", {"status": "pending"})
        force_authenticate(request, user=self.admin)

        response = AdminStudentsEnrollViews.as_view()(request)

        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], e1.id)

    def test_admin_enrollment_accept_bulk(self) -> None:
        e1 = StudentEnrollmentRequest.objects.create(
            user=self.st1,
            cohort=self.cohort1_2,
            status=EnrollmentStatus.PENDING,
        )
        e2 = StudentEnrollmentRequest.objects.create(
            user=self.st2,
            cohort=self.cohort2_1,
            status=EnrollmentStatus.PENDING,
        )
        e3 = StudentEnrollmentRequest.objects.create(
            user=self.st2,
            cohort=self.cohort1_1,
            status=EnrollmentStatus.ACCEPTED,  # 이미 처리됨
        )

        request = self.factory.post(
            "/admin/enrollments/accept",
            {"enrollments": [e1.id, e2.id, e3.id]},
            format="json",
        )
        force_authenticate(request, user=self.admin)

        response = AdminStudentEnrollAcceptView.as_view()(request)

        self.assertEqual(response.status_code, 200)

        e1.refresh_from_db()
        e2.refresh_from_db()
        e3.refresh_from_db()

        self.assertEqual(e1.status, EnrollmentStatus.ACCEPTED)
        self.assertEqual(e2.status, EnrollmentStatus.ACCEPTED)
        self.assertEqual(e3.status, EnrollmentStatus.ACCEPTED)

    def test_admin_enrollment_reject_bulk(self) -> None:
        e1 = StudentEnrollmentRequest.objects.create(
            user=self.st1,
            cohort=self.cohort1_2,
            status=EnrollmentStatus.PENDING,
        )
        e2 = StudentEnrollmentRequest.objects.create(
            user=self.st2,
            cohort=self.cohort2_1,
            status=EnrollmentStatus.PENDING,
        )

        request = self.factory.post(
            "/admin/enrollments/reject",
            {"enrollments": [e1.id, e2.id]},
            format="json",
        )
        force_authenticate(request, user=self.admin)

        response = AdminStudentEnrollRejectView.as_view()(request)

        self.assertEqual(response.status_code, 200)

        e1.refresh_from_db()
        e2.refresh_from_db()

        self.assertEqual(e1.status, EnrollmentStatus.REJECTED)
        self.assertEqual(e2.status, EnrollmentStatus.REJECTED)

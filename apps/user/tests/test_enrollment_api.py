from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.courses.models.cohorts_models import Cohort, CohortStatusChoices
from apps.courses.models.courses_models import Course
from apps.courses.views import AvailableCoursesAPIView
from apps.user.models import CohortStudent, StudentEnrollmentRequest
from apps.user.views.enrollemnt import EnrolledCoursesAPIView, EnrollStudentAPIView


class EnrollmentAPIViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            email="iwannabebedev@example.com",
            password="Pass1234!",
            name="Tester",
            birthday=timezone.localdate(),
            phone_number="01012341234",
            gender="M",
        )
        self.course = Course.objects.create(
            name="Backend Bootcamp",
            tag="BE",
            description="desc",
            thumbnail_img_url="https://example.com/thumb.png",
        )
        base_date = timezone.localdate()
        self.available_cohort = Cohort.objects.create(
            course=self.course,
            number=1,
            max_student=10,
            start_date=base_date + timedelta(days=3),
            end_date=base_date + timedelta(days=30),
            status=CohortStatusChoices.PENDING,
        )

    def test_enroll_student_creates_request(self) -> None:
        request = self.factory.post(
            "/api/v1/accounts/enroll-student",
            {"cohort_id": self.available_cohort.id},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = EnrollStudentAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(StudentEnrollmentRequest.objects.filter(user=self.user, cohort=self.available_cohort).exists())

    def test_enroll_student_rejects_duplicate(self) -> None:
        StudentEnrollmentRequest.objects.create(user=self.user, cohort=self.available_cohort)
        request = self.factory.post(
            "/api/v1/accounts/enroll-student",
            {"cohort_id": self.available_cohort.id},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = EnrollStudentAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_available_courses_returns_only_available(self) -> None:
        base_date = timezone.localdate()
        Cohort.objects.create(
            course=self.course,
            number=2,
            max_student=10,
            start_date=base_date - timedelta(days=10),
            end_date=base_date - timedelta(days=1),
            status=CohortStatusChoices.COMPLETED,
        )
        request = self.factory.get("/api/v1/courses/available")
        force_authenticate(request, user=self.user)

        response = AvailableCoursesAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        item = response.data[0]
        self.assertEqual(item["cohort"]["id"], self.available_cohort.id)
        self.assertEqual(item["course"]["id"], self.course.id)

    def test_enrolled_courses_returns_user_cohorts(self) -> None:
        CohortStudent.objects.create(user=self.user, cohort=self.available_cohort)
        request = self.factory.get("/api/v1/accounts/me/enrolled-courses")
        force_authenticate(request, user=self.user)

        response = EnrolledCoursesAPIView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        item = response.data[0]
        self.assertEqual(item["cohort"]["id"], self.available_cohort.id)
        self.assertEqual(item["course"]["tag"], "BE")

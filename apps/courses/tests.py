from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Cohort, Course
from apps.courses.models.cohorts_models import CohortStatusChoices


class CohortsListViewTest(APITestCase):
    def setUp(self) -> None:

        self.admin_user = get_user_model().objects.create_superuser(
            name="testuser",
            email="test@test.com",
            password="qwer1234!",
            birthday=date(2007, 8, 31),
        )
        self.client.force_authenticate(user=self.admin_user)

        self.course = Course.objects.create(
            name="테스트 과정",
            tag=1,
            description="테스트 과정",
        )

        self.active_cohort = Cohort.objects.create(
            course=self.course,
            number=1,
            max_student=10,
            start_date="2025-01-01",
            end_date="2025-12-31",
            status=CohortStatusChoices.IN_PROGRESS,
        )

        self.completed_cohort = Cohort.objects.create(
            course=self.course,
            number=2,
            max_student=10,
            start_date="2024-01-01",
            end_date="2024-12-31",
            status=CohortStatusChoices.COMPLETED,
        )

        self.url = reverse("course-cohort-list", kwargs={"course_id": self.course.id})

    def test_get_cohorts_success(self) -> None:
        """
        수강 중인 기수 목록 요청
        """
        expected_data = [
            {
                "id": self.active_cohort.id,
                "course": self.course.id,
                "course_name": self.course.name,
                "number": self.active_cohort.number,
                "cohort_display": "1기",
                "status": "IN_PROGRESS",
            }
        ]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data, expected_data)

    def test_get_cohorts_invalid_course(self) -> None:
        """
        존재하지 않는 과정 요청
        """
        invalid_url = reverse("course-cohort-list", kwargs={"course_id": 9999})
        response = self.client.get(invalid_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "과정 정보을(를) 찾을 수 없습니다.")

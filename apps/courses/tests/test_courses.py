from django.urls import reverse
from rest_framework import status

from apps.courses.models.cohorts_models import CohortStatusChoices
from apps.courses.tests.test_base import BaseCourseTestCase


class CohortsListViewTest(BaseCourseTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("course-cohort-list")

    def test_get_cohorts_success(self) -> None:
        """
        수강 중인 기수 목록 요청
        """
        expected_data = [
            {
                "id": self.course.id,
                "name": self.course.name,
                "cohorts": [
                    {
                        "id": self.active_cohort.id,
                        "number": self.active_cohort.number,
                        "display": "1기",
                        "status": "IN_PROGRESS",
                    },
                    {
                        "id": self.pending_cohort.id,
                        "number": self.pending_cohort.number,
                        "display": "3기",
                        "status": "PENDING",
                    },
                ],
            }
        ]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data, expected_data)

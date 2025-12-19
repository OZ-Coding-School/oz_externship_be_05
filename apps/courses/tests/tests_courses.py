from django.urls import reverse
from rest_framework import status

from apps.courses.models.cohorts_models import CohortStatusChoices
from apps.courses.tests.test_base import BaseCourseTestCase


class CohortsListViewTest(BaseCourseTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("course-cohort-list", kwargs={"course_id": self.course.id})

    def test_get_cohorts_success(self) -> None:
        """
        수강 중인 기수 목록 요청
        """
        expected_data = {
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

from django.urls import reverse
from rest_framework import status

from apps.courses.tests.test_base import BaseCourseTestCase


class CohortsListViewTest(BaseCourseTestCase):

    def setUp(self) -> None:
        super().setUp()
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

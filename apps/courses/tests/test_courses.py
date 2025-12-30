from django.urls import reverse
from rest_framework import status

from apps.courses.models import Course
from apps.courses.models.cohorts_models import Cohort, CohortStatusChoices
from apps.courses.serializers.courses_serializers import (
    CohortSerializer,
    CourseSerializer,
)
from apps.courses.tests.test_base import BaseCourseTestCase


class CourseListViewTest(BaseCourseTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("course-list")

    def test_CourseListView(self) -> None:
        """
        수강 목록 조회
        """
        courses = Course.objects.all()
        expected_data = CourseSerializer(courses, many=True).data

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)


class CohortListViewTest(BaseCourseTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("cohort-list")

    def test_CohortListView(self) -> None:
        """
        기수 목록 조회
        """
        cohorts = Cohort.objects.all()
        expected_data = CohortSerializer(cohorts, many=True).data

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)


class CohortListDetailViewTest(BaseCourseTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("cohort-list-detail", kwargs={"course_id": self.course.id})

    def test_CohortListViewDetail(self) -> None:
        """
        기수 목록 조회
        """
        cohorts = Cohort.objects.all()
        expected_data = CohortSerializer(cohorts, many=True).data

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

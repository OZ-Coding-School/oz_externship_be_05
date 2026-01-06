from django.urls import reverse
from rest_framework import status

from apps.courses.models import Course, Subject
from apps.courses.models.cohorts_models import Cohort
from apps.courses.serializers.courses_serializers import (
    CohortSerializer,
    CourseSerializer,
    SubjectSerializer,
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


class SubjectListDetailViewTest(BaseCourseTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("subject-list-detail", kwargs={"course_id": self.course.id})

    def test_CohortListViewDetail(self) -> None:
        """
        과목 목록 조회
        """

        subjects = Subject.objects.all()
        expected_data = SubjectSerializer(subjects, many=True).data

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

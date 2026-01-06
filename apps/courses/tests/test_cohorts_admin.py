from django.contrib.admin import AdminSite

from apps.courses.admin.cohorts_admin import CohortAdmin
from apps.courses.models import Cohort
from apps.courses.tests.test_base import BaseCourseTestCase


class CohortAdminTest(BaseCourseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.site = AdminSite()
        self.admin = CohortAdmin(Cohort, self.site)

    def test_display_max_student(self) -> None:
        """최대 인원 표시 테스트"""
        display_max_student = self.admin.display_max_student(self.active_cohort)
        self.assertEqual(display_max_student, "10명")

    def test_display_number(self) -> None:
        """기수 표시 테스트"""
        display_number = self.admin.display_number(self.active_cohort)
        self.assertEqual(display_number, "1기")

    def test_display_students(self) -> None:
        """등록 학생 표시 테스트"""
        display_students = self.admin.display_students(self.active_cohort)
        self.assertEqual(display_students, "학생 없음")

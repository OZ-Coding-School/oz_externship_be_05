from django.contrib.admin import AdminSite
from django.utils.safestring import SafeString

from apps.courses.admin.courses_admin import CourseAdmin
from apps.courses.models import Course
from apps.courses.tests.test_base import BaseCourseTestCase


class CoursesAdminTest(BaseCourseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.site = AdminSite()
        self.admin = CourseAdmin(Course, self.site)

    def test_currently_operating_cohorts(self) -> None:
        setattr(self.course, "_currently_operating_cohorts", [1, 2])
        currently_operating_cohorts = self.admin.currently_operating_cohorts(self.course)
        self.assertEqual(currently_operating_cohorts, "1, 2 기")

    def test_total_students(self) -> None:
        setattr(self.course, "_total_students", 3)
        total_students = self.admin.total_students(self.course)
        self.assertEqual(total_students, "3 명")

    def test_get_preview(self) -> None:
        """이미지가 있을 때 테스트"""
        preview_html = self.admin.get_preview(self.course)

        self.assertIsInstance(preview_html, SafeString)
        self.assertIn('<img src="https://example.com/test.jpg"', preview_html)

    def test_get_preview_without_image(self) -> None:
        """이미지 URL이 없을 때 테스트"""
        self.course.thumbnail_img_url = ""
        self.course.save()

        preview_text = self.admin.get_preview(self.course)
        self.assertEqual(preview_text, "(URL 없음)")

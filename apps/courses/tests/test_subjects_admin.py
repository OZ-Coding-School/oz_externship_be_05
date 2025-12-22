from django.contrib.admin import AdminSite
from django.utils.safestring import SafeString

from apps.courses.admin.subjects_admin import SubjectAdmin
from apps.courses.models import Subject
from apps.courses.tests.test_base import BaseCourseTestCase


class SubjectAdminTest(BaseCourseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.site = AdminSite()
        self.admin = SubjectAdmin(Subject, self.site)

    def test_display_number_of_days(self) -> None:
        """수강 일수 표시 테스트"""
        display_val = self.admin.display_number_of_days(self.subject)
        self.assertEqual(display_val, "5 일")

    def test_display_number_of_hours(self) -> None:
        """시수 표시 테스트"""
        display_val = self.admin.display_number_of_hours(self.subject)
        self.assertEqual(display_val, "40 시간")

    def test_get_preview_with_image(self) -> None:
        """이미지가 있을 때 테스트"""
        preview_html = self.admin.get_preview(self.subject)

        self.assertIsInstance(preview_html, SafeString)
        self.assertIn('<img src="https://example.com/test.jpg"', preview_html)

    def test_get_preview_without_image(self) -> None:
        """이미지 URL이 없을 때 테스트"""
        self.subject.thumbnail_img_url = ""
        self.subject.save()

        preview_text = self.admin.get_preview(self.subject)
        self.assertEqual(preview_text, "(URL 없음)")

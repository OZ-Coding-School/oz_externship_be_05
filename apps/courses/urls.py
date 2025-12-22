from django.urls import URLPattern, URLResolver, path

from apps.courses.views import CourseCohortsView

urlpatterns: list[URLPattern | URLResolver] = [
    path("<int:course_id>/cohorts", CourseCohortsView.as_view(), name="course-cohort-list"),
]

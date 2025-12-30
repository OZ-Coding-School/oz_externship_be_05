from django.urls import URLPattern, URLResolver, path

from apps.courses.views import (
    AvailableCoursesAPIView,
    CohortListView,
    CourseListView,
    SubjectListView,
)

urlpatterns: list[URLPattern | URLResolver] = [
    path("<int:course_id>/cohorts", CohortListView.as_view(), name="cohort-list-detail"),
    path("", CourseListView.as_view(), name="course-list"),
    path("<int:course_id>/subjects", SubjectListView.as_view(), name="subject-list-detail"),
    path("available", AvailableCoursesAPIView.as_view(), name="available-courses-list"),
]

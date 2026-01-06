from django.urls import URLPattern, URLResolver, path

from apps.courses.views import (
    AvailableCoursesAPIView,
    CohortListView,
    CourseListView,
    SubjectListView,
)

urlpatterns: list[URLPattern | URLResolver] = [
    path("courses/<int:course_id>/cohorts", CohortListView.as_view(), name="cohort-list-detail"),
    path("courses/<int:course_id>/subjects", SubjectListView.as_view(), name="subject-list-detail"),
    path("courses", CourseListView.as_view(), name="course-list"),
    path("courses/available", AvailableCoursesAPIView.as_view(), name="available-courses-list"),
]

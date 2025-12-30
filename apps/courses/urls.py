from django.urls import URLPattern, URLResolver, path

from apps.courses.views import AvailableCoursesAPIView, CohortListView, CourseListView

urlpatterns: list[URLPattern | URLResolver] = [
    path("<course_id>/cohorts", CohortListView.as_view(), name="cohort-list-detail"),
    path("cohorts", CohortListView.as_view(), name="cohort-list"),
    path("", CourseListView.as_view(), name="course-list"),
    path("available", AvailableCoursesAPIView.as_view(), name="available-courses-list"),
]

from django.urls import URLPattern, URLResolver, path

from apps.courses.views import CourseCohortsView, AvailableCoursesAPIView

urlpatterns: list[URLPattern | URLResolver] = [
    path("cohorts", CourseCohortsView.as_view(), name="course-cohort-list"),
    path("available",AvailableCoursesAPIView.as_view(),name="available-courses-list")
]

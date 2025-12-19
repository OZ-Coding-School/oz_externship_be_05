from django.urls import URLPattern, URLResolver, path

from apps.courses.views import CohortsListView

urlpatterns: list[URLPattern | URLResolver] = [
    path("<int:course_id>/cohorts", CohortsListView.as_view(), name="course-cohort-list"),
]

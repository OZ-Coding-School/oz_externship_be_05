from typing import Any

from django.db.models import Count, F, Q

from apps.community.admin.utils.filter import TimeOrderingFilter
from apps.courses.models.cohorts_models import CohortStatusChoices


class CourseOrderingFilter(TimeOrderingFilter):
    title = "정렬 기준"
    parameter_name = "courses_order_by"

    def lookups(self, request: Any, model_admin: Any) -> list[tuple[str, str]]:
        time_options = super().lookups(request, model_admin)

        course_options = [("most_student", "학생 많은 순"), ("most_cohorts", "기수 많은 순")]

        return time_options + course_options

    def queryset(self, request: Any, queryset: Any) -> Any:

        if self.value() == "most_student":
            return queryset.order_by(F("_total_students").desc(nulls_last=True))

        if self.value() == "most_cohorts":
            return queryset.annotate(
                _operating_cohorts_count=Count(
                    "cohorts", filter=Q(cohorts__status=CohortStatusChoices.IN_PROGRESS), distinct=True
                )
            ).order_by(F("_operating_cohorts_count").desc(nulls_last=True))
        return super().queryset(request, queryset)

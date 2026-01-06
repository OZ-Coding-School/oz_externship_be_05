from typing import TYPE_CHECKING, Any, Union

from django.contrib import admin
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, F, Q, QuerySet, Sum
from django.http import HttpRequest
from django.utils.safestring import SafeString, mark_safe

from apps.courses.admin.utils.filter import CourseOrderingFilter
from apps.courses.models import Course
from apps.courses.models.cohorts_models import CohortStatusChoices

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin as _ModelAdmin

    BaseAdmin = _ModelAdmin[Course]
else:
    from django.contrib.admin import ModelAdmin as BaseAdmin


@admin.register(Course)
class CourseAdmin(BaseAdmin):
    fields = (
        "id",
        "name",
        "tag",
        "description",
        "currently_operating_cohorts",
        "total_students",
        "thumbnail_img_url",
        "created_at",
        "updated_at",
    )
    list_display = (
        "id",
        "get_preview",
        "name",
        "description",
        "currently_operating_cohorts",
        "total_students",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "currently_operating_cohorts",
        "total_students",
    )
    search_fields = (
        "name",
        "tag",
        "description",
    )

    list_display_links = ("name",)

    list_filter = (CourseOrderingFilter,)

    date_hierarchy = "created_at"

    @admin.display(description="currently operating cohorts ")
    def currently_operating_cohorts(self, obj: Any) -> str:
        numbers = obj._currently_operating_cohorts
        if numbers:
            return ", ".join(map(str, numbers)) + " 기"
        return "N/A"

    @admin.display(description="total students")
    def total_students(self, obj: Any) -> Any:
        return f"{obj._total_students} 명"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Course]:
        qs = super().get_queryset(request)

        qs = qs.annotate(
            _currently_operating_cohorts=ArrayAgg(
                "cohorts__number",
                delimiter=", ",
                filter=Q(cohorts__status=CohortStatusChoices.IN_PROGRESS),
                distinct=True,
            ),
            _total_students=Sum(
                "cohorts__max_student",
                filter=(
                    Q(cohorts__status=CohortStatusChoices.IN_PROGRESS)
                    | Q(cohorts__status=CohortStatusChoices.COMPLETED)
                ),
            ),
        )

        return qs

    def get_preview(self, obj: Any) -> Union[str, SafeString]:
        image_url = obj.thumbnail_img_url
        if image_url:
            html = f'<img src="{image_url}" width="100" height="auto" style="border-radius: 3px; border: 1px solid #ccc;" />'
            return mark_safe(html)

        else:
            return "(URL 없음)"

    get_preview.short_description = "thumbnail"  # type: ignore[attr-defined]

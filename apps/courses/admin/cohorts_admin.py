from typing import TYPE_CHECKING

from django.contrib import admin

from apps.courses.models import Cohort

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin as _ModelAdmin

    BaseAdmin = _ModelAdmin[Cohort]
else:
    from django.contrib.admin import ModelAdmin as BaseAdmin


@admin.register(Cohort)
class CohortAdmin(BaseAdmin):
    list_display = (
        "id",
        "number",
        "max_student",
        "status",
        "start_date",
        "end_date",
        "created_at",
        "updated_at",
    )

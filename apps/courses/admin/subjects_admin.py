from typing import TYPE_CHECKING, Any, Union

from django.contrib import admin
from django.utils.safestring import SafeString, mark_safe

from apps.community.admin.utils.filter import TimeOrderingFilter
from apps.courses.models import Subject

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin as _ModelAdmin

    BaseAdmin = _ModelAdmin[Subject]
else:
    from django.contrib.admin import ModelAdmin as BaseAdmin


@admin.register(Subject)
class SubjectAdmin(BaseAdmin):
    fields = (
        "id",
        "title",
        "course",
        "number_of_days",
        "number_of_hours",
        "status",
        "thumbnail_img_url",
        "created_at",
        "updated_at",
    )

    list_display = (
        "id",
        "get_preview",
        "title",
        "display_number_of_days",
        "display_number_of_hours",
        "course",
        "status",
        "created_at",
        "updated_at",
    )

    readonly_fields = ("id", "created_at", "updated_at")

    search_fields = ("title",)

    list_display_links = ("title",)

    list_filter = (
        TimeOrderingFilter,
        "course",
        "status",
    )

    date_hierarchy = "created_at"

    @admin.display(description="수강 일수", ordering="number_of_days")
    def display_number_of_days(self, obj: Subject) -> str:
        return f"{obj.number_of_days} 일"

    @admin.display(description="시수", ordering="number_of_hours")
    def display_number_of_hours(self, obj: Subject) -> str:
        return f"{obj.number_of_hours} 시간"

    def get_preview(self, obj: Any) -> Union[str, SafeString]:
        image_url = obj.thumbnail_img_url
        if image_url:
            html = f'<img src="{image_url}" width="100" height="auto" style="border-radius: 3px; border: 1px solid #ccc;" />'
            return mark_safe(html)

        else:
            return "(URL 없음)"

    get_preview.short_description = "thumbnail"  # type: ignore[attr-defined]

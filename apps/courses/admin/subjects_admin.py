from typing import TYPE_CHECKING, Any, Union

from django.contrib import admin
from django.utils.safestring import SafeString, mark_safe

from apps.courses.models import Subject

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin as _ModelAdmin

    BaseAdmin = _ModelAdmin[Subject]
else:
    from django.contrib.admin import ModelAdmin as BaseAdmin


@admin.register(Subject)
class SubjectAdmin(BaseAdmin):
    list_display = (
        "id",
        "title",
        "number_of_days",
        "status",
        "get_preview",
        "created_at",
        "updated_at",
    )
    readonly_fields = ("created_at", "updated_at")

    def get_preview(self, obj: Any) -> Union[str, SafeString]:
        image_url = obj.thumbnail_img_url
        if image_url:
            html = f'<img src="{image_url}" width="100" height="auto" style="border-radius: 3px; border: 1px solid #ccc;" />'
            return mark_safe(html)

        else:
            return "(URL 없음)"

    get_preview.short_description = "thumbnail"  # type: ignore[attr-defined]

from typing import TYPE_CHECKING

from django.contrib import admin

from apps.community.admin.utils.filter import TimeOrderingFilter
from apps.community.models.post_category import PostCategory

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin as _ModelAdmin

    BaseAdmin = _ModelAdmin[PostCategory]
else:
    from django.contrib.admin import ModelAdmin as BaseAdmin


@admin.register(PostCategory)
class PostCategoryAdmin(BaseAdmin):
    fields = (
        "id",
        "name",
        "status",
        "created_at",
        "updated_at",
    )
    list_display = (
        "id",
        "name",
        "status",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
    search_fields = ("name",)
    list_filter = (TimeOrderingFilter,)
    date_hierarchy = "created_at"
    list_display_links = ("name",)

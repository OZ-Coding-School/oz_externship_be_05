from typing import TYPE_CHECKING

from django.contrib import admin

from apps.community.models.post_category import PostCategory

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin as _ModelAdmin

    BaseAdmin = _ModelAdmin[PostCategory]
else:
    from django.contrib.admin import ModelAdmin as BaseAdmin


@admin.register(PostCategory)
class PostCategoryAdmin(BaseAdmin):
    list_display = (
        "name",
        "status",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"

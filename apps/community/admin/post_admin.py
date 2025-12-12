from typing import TYPE_CHECKING

from django.contrib import admin
from apps.community.models.post import Post

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin as _ModelAdmin
    BaseAdmin = _ModelAdmin[Post]
else:
    from django.contrib.admin import ModelAdmin as BaseAdmin

@admin.register(Post)
class PostAdmin(BaseAdmin):
    list_display = (
        "author",
        "title",
        "category",
        "content",
        "view_count",
        "is_visible",
        "is_notice",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "view_count",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "author",
        "title",
        "content",
    )
    date_hierarchy = "created_at"

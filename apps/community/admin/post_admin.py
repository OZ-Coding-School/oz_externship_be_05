from typing import TYPE_CHECKING

from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http.request import HttpRequest

from apps.community.admin.utils.filter import CustomSearchFilter, PostOrderingFilter
from apps.community.admin.utils.inlines import (
    AttachmentInline,
    CommentInline,
    ImageInline,
)
from apps.community.models.post import Post

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin as _ModelAdmin

    BaseAdmin = _ModelAdmin[Post]
else:
    from django.contrib.admin import ModelAdmin as BaseAdmin


@admin.register(Post)
class PostAdmin(BaseAdmin):
    list_display = (
        "id",
        "title",
        "author__nickname",
        "category",
        "content",
        "view_count",
        "likes_count",
        "comment_count",
        "is_visible",
        "is_notice",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "id",
        "view_count",
        "likes_count",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "author__nickname",
        "title",
        "content",
    )
    inlines = [
        CommentInline,
        AttachmentInline,
        ImageInline,
    ]
    date_hierarchy = "created_at"

    # 타이틀 클릭으로 상세 페이지 열람
    list_display_links = ("title",)

    # 커스텀 필터
    list_filter = [PostOrderingFilter, CustomSearchFilter, "category"]

    @admin.display(description="likes count")
    def likes_count(self, obj: Post) -> int:
        if hasattr(obj, "likes_count"):
            return int(obj.likes_count)
        return 0

    @admin.display(description="comments count")
    def comment_count(self, obj: Post) -> int:
        if hasattr(obj, "comment_count"):
            return int(obj.comment_count)
        return 0

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        qs = super().get_queryset(request)
        return qs.annotate(
            comment_count=Count("post_comments"),
            likes_count=Count("post_likes"),
        )

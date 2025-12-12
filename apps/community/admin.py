from typing import TYPE_CHECKING, Any

from django.contrib import admin

from apps.community.models.post import Post
from apps.community.models.post_category import PostCategory


class CommunityArea(admin.AdminSite):
    site_header = "Community admin Area"
    site_title = "Community Admin Area"
    index_title = "Community Admin Area"

    def has_permission(self, request: Any) -> bool:
        return bool(
            request.user.is_active
            # and request.user.groups.filter(name='community_admin_group').exists()
        )

    """
    접근 권한 체크 is_active + community_admin_group (groups 섹션)
    """


community_admin_site = CommunityArea(name="community_admin")

if TYPE_CHECKING:
    """
    Missing type parameters for generic type "ModelAdmin"  [type-arg]
    오류 떠서 검색 결과 이렇게 해결하라고 했습니다..
    찾아보니까 django 버전이 낮아서 그렇다고 하는데 참고한 링크는 PR에 올려두겠습니다.
    """

    class PostAdmin(admin.ModelAdmin[Post]):
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

else:

    class PostAdmin(admin.ModelAdmin):
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


if TYPE_CHECKING:

    class PostCategoryAdmin(admin.ModelAdmin[PostCategory]):
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

else:

    class PostCategoryAdmin(admin.ModelAdmin):
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


community_admin_site.register(Post, PostAdmin)
community_admin_site.register(PostCategory, PostCategoryAdmin)

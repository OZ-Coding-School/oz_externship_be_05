from typing import TYPE_CHECKING

from django.contrib import admin
from django.utils.safestring import mark_safe

from apps.community.models.post_comment import PostComment
from apps.community.models.post_attachments import PostAttachment
from apps.community.models.post_images import PostImage


class CommentInline(admin.TabularInline): # type: ignore[type-arg]
    model = PostComment
    extra = 1
    fields = ('content', 'author', 'created_at',)
    readonly_fields = ('created_at',)

class AttachmentInline(admin.TabularInline): # type: ignore[type-arg]
    model = PostAttachment
    extra = 1
    fields = ('file_url', 'file_name')

class ImageInline(admin.TabularInline): # type: ignore[type-arg]
    model = PostImage
    extra = 1
    fields = ("img_url", 'get_preview',)
    readonly_fields = ('get_preview',)

    def get_preview(self, obj):
        image_url = obj.img_url
        if image_url:
            html = f'<img src="{image_url}" width="100" height="auto" style="border-radius: 3px; border: 1px solid #ccc;" />'
            return mark_safe(html)

        else:
            return '(URL 없음)'

    get_preview.short_description = '미리보기'
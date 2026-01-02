from typing import Any

from django.utils.html import strip_tags
from rest_framework import serializers

from apps.qna.models import Question
from apps.qna.serializers.common.author_serializer import AuthorSerializer
from apps.qna.services.question.question_list.category_utils import (
    CategoryInfo,
    build_category_info,
)


class QuestionListSerializer(serializers.ModelSerializer[Question]):
    category = serializers.SerializerMethodField()

    author = AuthorSerializer(read_only=True)

    content_preview = serializers.SerializerMethodField()
    answer_count = serializers.IntegerField()

    thumbnail_img_url = serializers.URLField(
        source="thumbnail_image_url",
        allow_null=True,
    )

    _category_cache: dict[int, CategoryInfo]

    class Meta:
        model = Question
        fields = [
            "id",
            "category",
            "author",
            "title",
            "content_preview",
            "answer_count",
            "view_count",
            "created_at",
            "thumbnail_img_url",
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._category_cache = {}

    def get_category(self, obj: Question) -> CategoryInfo:
        category_id = obj.category_id

        if category_id not in self._category_cache:
            self._category_cache[category_id] = build_category_info(obj.category)

        return self._category_cache[category_id]

    # obj.content_preview가 존재하면 태그를 제거하고 반환, 없으면 빈 문자열
    def get_content_preview(self, obj: Question) -> str:
        content = getattr(obj, "content_preview", "")
        return strip_tags(content)

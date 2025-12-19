from typing import Any

from rest_framework import serializers

from apps.qna.models import Question
from apps.qna.services.question.question_list.category_utils import (
    CategoryPath,
    build_category_path,
)


class QuestionListSerializer(serializers.ModelSerializer[Question]):
    question_id = serializers.IntegerField(source="id")

    category_path = serializers.SerializerMethodField()

    profile_img_url = serializers.CharField(
        source="author.profile_image_url",
        allow_null=True,
    )
    nickname = serializers.CharField(source="author.nickname")

    content_preview = serializers.CharField()
    answer_count = serializers.IntegerField()

    thumbnail_img_url = serializers.URLField(
        source="thumbnail_image_url",
        allow_null=True,
    )

    # 요청 단위 캐시 타입 명시
    _category_path_cache: dict[int, CategoryPath]

    class Meta:
        model = Question
        fields = [
            "question_id",
            "category_path",
            "profile_img_url",
            "nickname",
            "title",
            "content_preview",
            "answer_count",
            "view_count",
            "created_at",
            "thumbnail_img_url",
        ]

    # Serializer 인스턴스 생성 시 요청 단위 캐시 공간 초기화
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._category_path_cache = {}

    def get_category_path(self, obj: Question) -> str:
        category_id = obj.category_id

        # 캐시에 없으면 계산
        if category_id not in self._category_path_cache:
            self._category_path_cache[category_id] = build_category_path(obj.category)

        # 있으면 그대로 재사용 / dict 전체가 아닌 문자열만 뽑음
        return self._category_path_cache[category_id]["path"]

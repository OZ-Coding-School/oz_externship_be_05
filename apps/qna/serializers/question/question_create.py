from typing import Any, Dict

from rest_framework import serializers

from apps.qna.models import Question, QuestionCategory, QuestionImage
from apps.qna.permissions.question.question_create_permission import (
    validate_question_category,
    validate_question_create_permission,
    validate_question_title_unique,
)
from apps.qna.services.question.question_create_service import create_question
from apps.user.models import User


class QuestionImageCreateSerializer(serializers.ModelSerializer[QuestionImage]):
    class Meta:
        model = QuestionImage
        fields = ["img_url"]


class QuestionCreateSerializer(serializers.ModelSerializer[Question]):
    category = serializers.IntegerField()

    image_urls = serializers.ListField(
        child=serializers.URLField(),
        write_only=True,
        required=False,
    )

    images = QuestionImageCreateSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "content",
            "category",
            "image_urls",
            "images",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        request = self.context["request"]
        user: User = request.user

        validate_question_create_permission(user)

        validate_question_title_unique(attrs.get("title"))

        category_id = attrs.get("category")
        if not isinstance(category_id, int):  # mypy 때문에 추가
            raise serializers.ValidationError({"type": "invalid_request"})

        validate_question_category(category_id)

        attrs["category"] = QuestionCategory.objects.get(id=category_id)

        return attrs

    def create(self, validated_data: Dict[str, Any]) -> Question:
        request = self.context["request"]

        image_urls = validated_data.pop("image_urls", [])

        return create_question(
            author=request.user,
            image_urls=image_urls,
            **validated_data,
        )

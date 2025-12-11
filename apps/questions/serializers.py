from typing import Any, Dict

from rest_framework import serializers

from apps.questions.models import Question, QuestionCategory, QuestionImage


class QuestionImageCreateSerializer(serializers.ModelSerializer[QuestionImage]):
    class Meta:
        model = QuestionImage
        fields = ["img_url"]


class QuestionCreateSerializer(serializers.ModelSerializer[Question]):
    category = serializers.PrimaryKeyRelatedField(queryset=QuestionCategory.objects.all())

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
            "image_urls",  # 요청
            "images",  # 응답
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data: Dict[str, Any]) -> Question:
        request = self.context["request"]

        image_urls = validated_data.pop("image_urls", [])

        question = Question.objects.create(author=request.user, **validated_data)

        for url in image_urls:
            QuestionImage.objects.create(question=question, img_url=url)

        return question

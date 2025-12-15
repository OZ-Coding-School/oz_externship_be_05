from rest_framework import serializers

from apps.qna.models import Question


class QuestionCreateSerializer(serializers.ModelSerializer[Question]):
    category = serializers.IntegerField()

    image_urls = serializers.ListField(
        child=serializers.URLField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Question
        fields = [
            "title",
            "content",
            "category",
            "image_urls",
        ]

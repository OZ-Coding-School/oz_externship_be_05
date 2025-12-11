from rest_framework import serializers

from apps.questions.models import Question, QuestionImage


class QuestionImageSpecSerializer(serializers.ModelSerializer[QuestionImage]):
    class Meta:
        model = QuestionImage
        fields = ["img_url"]


class QuestionCreateSpecSerializer(serializers.ModelSerializer[Question]):
    category = serializers.IntegerField()  # specapi에서만 잠시 변경

    image_urls = serializers.ListField(
        child=serializers.CharField(),
        # child=serializers.URLField(),
        write_only=True,
        required=False,
    )

    images = QuestionImageSpecSerializer(many=True, read_only=True)

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

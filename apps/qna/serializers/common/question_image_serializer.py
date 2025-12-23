from rest_framework import serializers

from apps.qna.models import QuestionImage


class QuestionImageSerializer(serializers.ModelSerializer[QuestionImage]):
    class Meta:
        model = QuestionImage
        fields = [
            "id",
            "img_url",
        ]

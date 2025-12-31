from rest_framework import serializers

from apps.qna.models import Question, QuestionCategory


class QuestionCreateSerializer(serializers.ModelSerializer[Question]):
    category = serializers.PrimaryKeyRelatedField(queryset=QuestionCategory.objects.all())

    class Meta:
        model = Question
        fields = [
            "title",
            "content",
            "category",
        ]

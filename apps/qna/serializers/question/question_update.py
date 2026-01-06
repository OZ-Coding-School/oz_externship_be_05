from rest_framework import serializers

from apps.qna.models import Question, QuestionCategory


class QuestionUpdateSerializer(serializers.ModelSerializer[Question]):

    class Meta:
        model = Question
        fields = [
            "title",
            "content",
            "category",
        ]

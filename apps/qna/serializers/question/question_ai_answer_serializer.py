from rest_framework import serializers

from apps.qna.models.question.question_ai_answer import QuestionAIAnswer


class QuestionAIAnswerSerializer(serializers.ModelSerializer[QuestionAIAnswer]):
    class Meta:
        model = QuestionAIAnswer
        fields = ["id", "question", "output", "using_model", "created_at"]
        extra_kwargs = {
            "id": {"read_only": True},
            "question": {"read_only": True},
            "output": {"read_only": True},
            "created_at": {"read_only": True},
            "using_model": {"read_only": True},
        }

from django.db import models

from apps.qna.models.question.question_base import Question


class QuestionAIAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="ai_answers")

    output = models.TextField()

    USING_MODEL_CHOICES = [
        ("GPT", "GPT"),
        ("GEMINI", "GEMINI"),
    ]

    using_model = models.CharField(max_length=30, choices=USING_MODEL_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "question_ai_answers"

    def __str__(self) -> str:
        return f"AI Answer for Question {self.question_id}"
from typing import Optional

from django.db import models

from apps.core.models import TimeStampedModel
from apps.qna.models.question.question_base import Question


class QuestionAIAnswer(TimeStampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="ai_answers")
    question_id: Optional[int]

    output = models.TextField()

    USING_MODEL_CHOICES = [
        ("GPT", "GPT"),
        ("GEMINI", "GEMINI"),
    ]

    using_model = models.CharField(max_length=30, choices=USING_MODEL_CHOICES)

    class Meta:
        db_table = "question_ai_answers"

    def __str__(self) -> str:
        return f"AI Answer for Question {self.question_id}"

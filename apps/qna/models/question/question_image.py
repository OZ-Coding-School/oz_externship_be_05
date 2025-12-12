from typing import Optional

from django.db import models

from apps.core.models import TimeStampedModel
from apps.qna.models.question.question_base import Question


class QuestionImage(TimeStampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="images")
    question_id: Optional[int]

    img_url = models.CharField(max_length=255)

    class Meta:
        db_table = "question_images"

    def __str__(self) -> str:
        return f"Image for Question {self.question_id}"

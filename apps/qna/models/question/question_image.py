from django.db import models

from apps.qna.models.question.question_base import Question


class QuestionImage(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="images")

    img_url = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "question_images"

    def __str__(self) -> str:
        return f"Image for Question {self.question_id}"
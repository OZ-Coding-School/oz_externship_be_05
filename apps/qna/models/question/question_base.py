from django.conf import settings
from django.db import models

from apps.qna.models.question.question_category import QuestionCategory


class Question(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questions")

    category = models.ForeignKey(QuestionCategory, on_delete=models.PROTECT, related_name="questions")

    title = models.CharField(max_length=50)
    content = models.TextField()

    view_count = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "questions"

    def __str__(self) -> str:
        return self.title

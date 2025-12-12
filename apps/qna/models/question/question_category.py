from django.db import models

from apps.core.models import TimeStampedModel


class QuestionCategory(TimeStampedModel):
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    name = models.CharField(max_length=15)

    class Meta:
        db_table = "question_categories"

    def __str__(self) -> str:
        return self.name

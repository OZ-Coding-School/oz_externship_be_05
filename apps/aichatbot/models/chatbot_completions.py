from django.db import models
from apps.core.models import TimeStampedModel

# ENUM용 클래스 - 유저
class UserRole(models.TextChoices):
    USER = "user", "USER"
    ASSISTANT = "assistant", "ASSISTANT"


class ChatbotCompletion(models.Model):
    session = models.ForeignKey("ChatbotSession", on_delete=models.CASCADE)
    message = models.TextField()
    role = models.TextField(choices=UserRole.choices)
    created_at = TimeStampedModel()
    updated_at = TimeStampedModel()

    class Meta:
        db_table = "chatbot_completions"

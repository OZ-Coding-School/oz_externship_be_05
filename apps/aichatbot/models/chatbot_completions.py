from django.db import models
from apps.core.models import TimeStampedModel

# ENUM용 클래스 - 유저
class UserRole(models.TextChoices):
    USER = "user", "USER"
    ASSISTANT = "assistant", "ASSISTANT"


class ChatbotCompletion(TimeStampedModel):
    session = models.ForeignKey("ChatbotSession", on_delete=models.CASCADE, related_name="messages")
    message = models.TextField()
    role = models.CharField(choices=UserRole.choices, max_length=9)
    created_at = TimeStampedModel()
    updated_at = TimeStampedModel()

    class Meta:
        db_table = "chatbot_completions"

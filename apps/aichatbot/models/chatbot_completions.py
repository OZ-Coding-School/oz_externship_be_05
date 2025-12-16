from django.db import models

from apps.core.models import TimeStampedModel


# ENUM용 클래스 - 유저
class UserRole(models.TextChoices):
    USER = "user", "USER"
    ASSISTANT = "assistant", "ASSISTANT"


# objects 선언: 이미 매니저가 할당되어 있지만 mypy용으로 명시적 선언 함
class ChatbotCompletion(TimeStampedModel):
    objects: models.Manager["ChatbotCompletion"] = models.Manager()
    session = models.ForeignKey("ChatbotSession", on_delete=models.CASCADE, related_name="messages")
    message = models.TextField()
    role = models.CharField(choices=UserRole.choices, max_length=9)

    class Meta:
        db_table = "chatbot_completions"

from django.db import models


# ENUM용 클래스 - 유저
class UserRole(models.TextChoices):
    USER = "user", "USER"
    ASSISTANT = "assistant", "ASSISTANT"


class ChatbotCompletion(models.Model):
    session = models.ForeignKey("chatbot_sessions.ChatbotSessions", on_delete=models.CASCADE)
    message = models.TextField()
    role = models.CharField(choices=UserRole.choices, max_length=14)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chatbot_completions"

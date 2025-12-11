from django.db import models
from apps.core.models import TimeStampedModel

# enum용 클래스 - 사용모델
class ChatModel(models.TextChoices):
    GEMINI = "gemini", "GEMINI 2.7"
    OPENAI = "openai", "OPENAI 4.7"


class ChatbotSession(models.Model):
    user = models.ForeignKey("user.User", on_delete=models.CASCADE, db_index=True)
    question = models.ForeignKey("questions.Question", on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=30)
    using_model = models.TextChoices(ChatModel.choices)
    created_at = TimeStampedModel().created_at
    updated_at = TimeStampedModel().updated_at

    class Meta:
        db_table = "chatbot_session"
        ordering = ("-created_at", "-id")
        # indexes = [
        #     models.Index(fields=["user"], name="idx"),
        #     models.Index(),
        # ]
        # 이 방식은 잘 모르겠어요

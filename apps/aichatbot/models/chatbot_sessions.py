from django.db import models

from apps.core.models import TimeStampedModel


# enum용 클래스 - 사용모델
class ChatModel(models.TextChoices):
    GEMINI = "gemini", "GEMINI 2.7"
    OPENAI = "openai", "OPENAI 4.7"


# objects 선언: 이미 매니저가 할당되어 있지만 mypy용으로 명시적 선언 함
class ChatbotSession(TimeStampedModel):
    objects: models.Manager["ChatbotSession"] = models.Manager()

    user = models.ForeignKey("user.User", on_delete=models.CASCADE, db_index=True)
    question = models.ForeignKey("qna.Question", on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=30)
    using_model = models.CharField(choices=ChatModel.choices, max_length=16)

    class Meta:
        db_table = "chatbot_sessions"
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(fields=("user", "question"), name="user_question_unique"),
        ]

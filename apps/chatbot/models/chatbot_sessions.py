from django.db import models

from apps.core.models import TimeStampedModel


# enum용 클래스 - 사용모델
class ChatModel(models.TextChoices):
    GEMINI = "gemini-2.5-flash", "gemini"
    OPENAI = "openai-o4-mini", "openai"


class ChatbotSession(TimeStampedModel):
    user = models.ForeignKey("user.User", on_delete=models.CASCADE)
    question = models.ForeignKey("qna.Question", on_delete=models.CASCADE)
    title = models.CharField(max_length=30)
    using_model = models.CharField(choices=ChatModel.choices, max_length=20)

    class Meta:
        db_table = "chatbot_sessions"
        constraints = [
            models.UniqueConstraint(fields=("user", "question"), name="user_question_unique"),
        ]

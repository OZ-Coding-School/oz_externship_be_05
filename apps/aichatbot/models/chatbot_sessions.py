from django.db import models


# enum용 클래스 - 사용모델
class ChatModel(models.TextChoices):
    GEMINI = "gemini", "GEMINI 2.7"
    OPENAI = "openai", "OPENAI 4.7"


class ChatbotSession(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    question = models.ForeignKey("questions.Question", on_delete=models.CASCADE)
    title = models.CharField(max_length=30)
    using_model = models.CharField(choices=ChatModel.choices, max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chatbot_session"

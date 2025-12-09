from django.db import models


# enum용 클래스 - 사용모델
class ChatModel(models.TextChoices):
    GEMINI = "gemini", "GEMINI 2.7"
    OPENAI = "openai", "OPENAI 4.7"


class ChatbotSession(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    question = models.ForeignKey("questions.Question", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chatbot_session"


# null=False는 기본이래여..
class ChatbotCompletion(models.Model):
    session_id = models.ForeignKey("chatbot_sessions.ChatbotSessions", on_delete=models.CASCADE)
    prompt = models.TextField()
    output = models.TextField()
    using_model = models.CharField(choices=ChatModel.choices, max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chatbot_completions"
        # verbose_name =  "무언가"
        # verbose_name_plural = "무언가"
        # 굳이 안 적어도 될듯?

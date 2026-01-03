from django.db import models

from apps.core.models import TimeStampedModel
from apps.chatbot.models.chatbot_sessions import ChatModel

class QuestionAIAnswer(TimeStampedModel):
    question = models.ForeignKey("qna.Question", on_delete=models.CASCADE)
    output = models.TextField()
    using_model = models.CharField(choices=ChatModel.choices, max_length=20)

    class Meta:
        db_table = "question_ai_answers"
from django.conf import settings
from django.db import models


class QuestionCategory(models.Model):
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    name = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "question_categories"

    def __str__(self) -> str:
        return self.name


class Question(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questions")

    category = models.ForeignKey(QuestionCategory, on_delete=models.PROTECT, related_name="questions")

    title = models.CharField(max_length=50)
    content = models.TextField()

    view_count = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "questions"

    def __str__(self) -> str:
        return self.title


class QuestionImage(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="images")

    img_url = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "question_images"

    def __str__(self) -> str:
        return f"Image for Question {self.question_id}"


class QuestionAIAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="ai_answers")

    output = models.TextField()

    USING_MODEL_CHOICES = [
        ("GPT", "GPT"),
        ("GEMINI", "GEMINI"),
    ]

    using_model = models.CharField(max_length=30, choices=USING_MODEL_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "question_ai_answers"

    def __str__(self) -> str:
        return f"AI Answer for Question {self.question_id}"

from django.db import models

# 날릴겁니다 이거 더미데이터용으로 쓸 것


class Question(models.Model):
    author = models.ForeignKey("users.User", on_delete=models.CASCADE)
    category = models.ForeignKey("questions.Category", on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    content = models.TextField()
    view_count = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "question"

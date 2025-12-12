from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Answer(TimeStampedModel):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # 작성자가 삭제되면 답변도 삭제
        related_name="answers_authored",
        help_text="답변 작성자 ID",
    )

    question = models.ForeignKey(
        "questions.Question",
        on_delete=models.CASCADE,  # 답변이 속한 질문이 삭제되면 답변도 삭제
        related_name="answers",
        help_text="답변이 속한 질문 ID",
    )

    content = models.TextField(help_text="답변 내용 본문")
    is_adopted = models.BooleanField(default=False, help_text="채택 여부")

    class Meta:
        db_table = "answers"
        verbose_name = "답변"
        verbose_name_plural = "답변 목록"
        ordering = ["-created_at"]  # 최신 답변이 먼저 오도록 정렬

    def __str__(self) -> str:
        return f"{self}번 답변 (Q: {self.question})"

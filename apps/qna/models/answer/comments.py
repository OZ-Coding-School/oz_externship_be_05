from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class AnswerComment(TimeStampedModel):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # 작성자가 삭제되면 댓글도 삭제
        related_name="answer_comments",  # 유저입장에서 쓴 댓글들
        help_text="댓글 작성자 ID",
    )

    answer = models.ForeignKey(
        "qna.Answer",  # Answer 모델 참조
        on_delete=models.CASCADE,  # 댓글이 달린 답변이 삭제되면 댓글도 삭제
        related_name="comments",
        help_text="댓글이 달린 답변 ID",
    )

    content = models.CharField(max_length=500, help_text="댓글 내용 본문")

    class Meta:
        app_label = "qna"
        db_table = "answer_comments"

    def __str__(self) -> str:
        return f"{self.pk}번 댓글 (by {self.author_id})"  # 작성자가 누구인지빠르게 파악

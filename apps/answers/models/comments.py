from django.conf import settings
from django.db import models


class AnswerComment(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # 작성자가 삭제되면 댓글도 삭제
        related_name="comments_authored",
        help_text="댓글 작성자 ID",
    )

    answer = models.ForeignKey(
        "answers.Answer",  # Answer 모델 참조
        on_delete=models.CASCADE,  # 댓글이 달린 답변이 삭제되면 댓글도 삭제
        related_name="comments",
        help_text="댓글이 달린 답변 ID",
    )

    content = models.CharField(max_length=500, help_text="댓글 내용 본문")
    created_at = models.DateTimeField(auto_now_add=True, help_text="작성 시간")
    updated_at = models.DateTimeField(auto_now=True, help_text="수정 시간")

    class Meta:
        db_table = "answers_comments"
        verbose_name = "답변 댓글"
        verbose_name_plural = "답변 댓글 목록"
        ordering = ["-created_at"]  # 최신 댓글이 먼저 오도록 정렬

    # def __str__(self) -> str:
    #     return f"{self.id}번 댓글 (A: {self.answer.id})"

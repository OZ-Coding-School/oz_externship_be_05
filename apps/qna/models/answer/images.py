from django.conf import settings
from django.db import models


class AnswerImage(models.Model):
    answer = models.ForeignKey(
        "answers.Answer",  # Answer 모델 참조
        on_delete=models.CASCADE,  # 답변이 삭제되면 이미지도 삭제
        related_name="images",
        help_text="이미지가 속한 답변 ID",
    )

    image_url = models.ImageField(upload_to="answer_images/", help_text="답변 이미지 파일")
    uploaded_at = models.DateTimeField(auto_now_add=True, help_text="업로드 시간")
    updated_at = models.DateTimeField(auto_now=True, help_text="수정 시간")

    class Meta:
        db_table = "answers_images"
        verbose_name = "답변 이미지"
        verbose_name_plural = "답변 이미지 목록"
        ordering = ["-uploaded_at"]  # 최신 이미지가 먼저 오도록 정렬

    # def __str__(self) -> str:
    #     return f"{self.id}번 이미지 (A: {self.answer.id})"

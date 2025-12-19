from django.db import models
from apps.core.models import TimeStampedModel
from apps.qna.models.answer.answers import Answer


class AnswerImage(TimeStampedModel):
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,  # 답변이 삭제되면 이미지도 삭제
        related_name="images",
        # 프론트엔드단에서 s3통한 동시생성으로 Null,blank 삭제
        help_text="이미지가 속한 답변 ID",
    )

    image_url = models.CharField(
        max_length=500,
        help_text="S3 object Key",
    )

    class Meta:
        app_label = "qna"
        db_table = "answers_images"
        verbose_name = "답변 이미지"
        verbose_name_plural = "답변 이미지 목록"
        ordering = ["-created_at"]  

    def __str__(self) -> str:
        return f"{self.pk}번 이미지 (on Answer {self.answer_id}) - {self.image_url}"  # 어떤 답변에 붙은이미지인지 식별

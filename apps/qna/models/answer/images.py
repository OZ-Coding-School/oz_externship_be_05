from django.conf import settings
from django.core.validators import RegexValidator
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
        max_length=255,
        help_text="이미지 파일 경로 URL",
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^answer_images/", message="이미지 경로는 반드시 'answer_images/'로 시작하는 S3 Key여야 합니다"
            )
        ],
    )

    class Meta:
        app_label = "qna"
        db_table = "answers_images"
        verbose_name = "답변 이미지"
        verbose_name_plural = "답변 이미지 목록"
        ordering = ["-created_at"]  # 최신 이미지가 먼저 오도록 정렬

    def __str__(self) -> str:
        return f"{self.pk}번 이미지 (on Answer {self.answer_id}) - {self.image_url}"  # 어떤 답변에 붙은이미지인지 식별

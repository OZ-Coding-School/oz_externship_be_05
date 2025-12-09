from django.db import models

from ...core.models import TimeStampedModel


class Exam(TimeStampedModel):
    """
    쪽지시험 기본 정보
    ERD: exams
    """

    # ERD: subject_id bigint [not null]
    subject = models.ForeignKey(
        "apps.Subjects",
        on_delete=models.PROTECT,
        related_name="exams",
    )

    # ERD: title varchar(50) [not null]
    title = models.CharField(max_length=50)

    # ERD: thumbnail_img_url varchar(255) [not null, default: 'default_img_url']
    thumbnail_img_url = models.CharField(
        max_length=255,
        default="default_img_url",
    )

    class Meta:
        db_table = "exams"
        verbose_name = "Exam"
        verbose_name_plural = "Exams"

    def __str__(self) -> str:
        return f"{self.title} (id={self.pk})"
from django.db import models


class CohortsChoices(models.TextChoices):
    PENDING = "PENDING", "대기중"
    IN_PROGRESS = "IN_PROGRESS", "처리중"
    COMPLETED = "COMPLETED", "처리완료"


class Cohorts(models.Model):
    course_id = models.BigIntegerField()
    number = models.PositiveIntegerField()
    max_student = models.PositiveIntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    status = models.CharField(
        choices=CohortsChoices.choices,
        default=CohortsChoices.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cohorts"

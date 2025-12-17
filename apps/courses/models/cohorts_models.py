from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models.courses_models import Course


class CohortStatusChoices(models.TextChoices):
    PENDING = "PENDING", "대기중"
    IN_PROGRESS = "IN_PROGRESS", "수강중"
    COMPLETED = "COMPLETED", "수료"


class Cohort(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="cohorts")
    number = models.SmallIntegerField(
        validators=[MinValueValidator(1)],
    )
    max_student = models.SmallIntegerField(
        validators=[MinValueValidator(1)],
    )
    end_date = models.DateField()
    start_date = models.DateField()
    status = models.CharField(
        choices=CohortStatusChoices.choices,
        default=CohortStatusChoices.PENDING,
    )

    def __str__(self) -> str:
        return self.course.name

    class Meta:
        verbose_name = "Cohort"
        verbose_name_plural = "Cohorts"
        db_table = "cohorts"
        constraints = [
            models.CheckConstraint(check=models.Q(number__gte=1), name="number_non_negative"),
            models.CheckConstraint(check=models.Q(max_student__gte=1), name="max_student_non_negative"),
        ]

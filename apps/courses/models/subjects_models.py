from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models.courses_models import Course


class SubjectChoices(models.TextChoices):
    activated = "activated"
    deactivated = "deactivated"


class Subject(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=30, unique=True)
    number_of_days = models.SmallIntegerField(
        validators=[MinValueValidator(1)],
    )
    number_of_hours = models.SmallIntegerField(
        validators=[MinValueValidator(1)],
    )
    thumbnail_img_url = models.URLField(null=True, blank=True)
    status = models.CharField(
        choices=SubjectChoices.choices,
        default=SubjectChoices.deactivated,
    )

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        db_table = "subjects"
        constraints = [
            models.CheckConstraint(check=models.Q(number_of_days__gte=1), name="number_of_days_non_negative"),
            models.CheckConstraint(check=models.Q(number_of_hours__gte=1), name="number_of_hours_non_negative"),
        ]

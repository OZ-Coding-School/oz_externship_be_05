from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models.courses_models import Course


class SubjectChoices(models.TextChoices):
    PENDING = "PENDING", "대기중"
    IN_PROGRESS = "IN_PROGRESS", "처리중"
    COMPLETED = "COMPLETED", "처리완료"


class Subject(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=30, unique=True)
    number_of_days = models.SmallIntegerField()
    number_of_hours = models.SmallIntegerField()
    thumbnail_img_url = models.URLField(null=True, blank=True)
    status = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        db_table = "subjects"

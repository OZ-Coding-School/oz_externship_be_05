from django.db import models

from apps.core.models import TimeStampedModel


class Course(TimeStampedModel):
    name = models.CharField(max_length=30)
    tag = models.CharField(max_length=3)
    description = models.CharField(max_length=255)
    thumbnail_img_url = models.URLField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        db_table = "courses"

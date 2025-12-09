from django.db import models

from apps.core.models import TimeStampedModel


class Course(TimeStampedModel):
    name = models.CharField(max_length=30)
    tag = models.CharField(max_length=3)
    description = models.CharField(max_length=255)
    thumbnail_img_url = models.URLField(null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courses"

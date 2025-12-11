from django.db import models

from apps.core.models import TimeStampedModel


class PostCategory(TimeStampedModel):
    name = models.CharField(max_length=20)
    status = models.BooleanField(default=False)

    class Meta:
        db_table = "post_category"

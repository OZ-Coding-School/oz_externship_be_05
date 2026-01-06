from django.db import models

from apps.core.models import TimeStampedModel


class PostCategory(TimeStampedModel):
    name = models.CharField(max_length=20)
    status = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Post Category"
        verbose_name_plural = "Post Category"
        db_table = "post_category"

from django.db import models

from apps.core.models import TimeStampedModel
from apps.community.models.post import Post


class PostImage(TimeStampedModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    img_url = models.URLField()

    class Meta:
        db_table = "post_images"

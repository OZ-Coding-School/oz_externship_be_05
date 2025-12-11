from django.db import models

from apps.community.models.post import Post
from apps.core.models import TimeStampedModel


class PostImage(TimeStampedModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    img_url = models.URLField()

    class Meta:
        db_table = "post_images"

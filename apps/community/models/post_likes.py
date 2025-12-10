from django.db import models

from apps.core.models import TimeStampedModel
from apps.community.models.post import Post
from apps.user.models import User


class PostLike(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    is_like = models.BooleanField(default=True)

    class Meta:
        db_table = "post_like"
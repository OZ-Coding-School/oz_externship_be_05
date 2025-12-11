from django.db import models

from apps.community.models.post import Post
from apps.user.models import User
from apps.core.models import TimeStampedModel


class PostComment(TimeStampedModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    content = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "post_comments"

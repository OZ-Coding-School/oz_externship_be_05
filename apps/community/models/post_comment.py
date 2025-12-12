from django.db import models

from apps.community.models.post import Post
from apps.core.models import TimeStampedModel
from apps.user.models import User

#apps/community/models/post_comment.py
class PostComment(TimeStampedModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_comments")
    content = models.CharField(max_length=300)

    class Meta:
        db_table = "post_comments"

from django.db import models

from apps.community.models.post_comment import PostComment
from apps.user.models import User
from apps.core.models import TimeStampedModel


class PostCommentTag(TimeStampedModel):
    tagged_user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "post_comment_tags"

from django.db import models

from apps.community.models.post_comment import PostComment
from apps.core.models import TimeStampedModel
from apps.user.models import User


class PostCommentTag(TimeStampedModel):
    tagged_user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "post_comment_tags"

from django.db import models

from apps.community.models.post_comment import PostComment
from apps.core.models import TimeStampedModel
from apps.user.models import User

class PostCommentTag(TimeStampedModel):
    tagged_user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE)

    class Meta:
        db_table = "post_comment_tags"
        unique_together = ["comment", "tagged_user"]
